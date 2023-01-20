# -*- coding: utf-8 -*-
import abc
import logging
from contextlib import contextmanager
from threading import RLock
from typing import Any, TYPE_CHECKING, Type, Union, TypeVar

from sceptre.helpers import _call_func_on_values
from sceptre.resolvers.placeholders import (
    create_placeholder_value,
    are_placeholders_enabled,
    PlaceholderType,
)

if TYPE_CHECKING:
    from sceptre import stack

T_Container = TypeVar("T_Container", bound=Union[dict, list])


class RecursiveResolve(Exception):
    pass


class Resolver(abc.ABC):
    """
    Resolver is an abstract base class that should be inherited by all
    Resolvers.

    :param argument: The argument of the resolver.
    :param stack: The associated stack of the resolver.
    """

    def __init__(self, argument: Any = None, stack: "stack.Stack" = None):
        self.logger = logging.getLogger(__name__)
        self.argument = argument
        self.stack = stack

    def setup(self):
        """
        This method is called at during stack initialisation.
        Implementation of this method in subclasses can be used to do any
        initial setup of the object.
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def resolve(self):
        """
        An abstract method which must be overwritten by all inheriting classes.
        This method is called to retrieve the final desired value.
        Implementation of this method in subclasses must return a suitable
        object or primitive type.
        """
        pass  # pragma: no cover

    def clone(self, stack: "stack.Stack") -> "Resolver":
        """
        Produces a "fresh" copy of the Resolver, with the specified stack.

        :param stack: The stack to set on the cloned resolver
        """
        return type(self)(self.argument, stack)


class ResolvableProperty(abc.ABC):
    """
    This is an abstract base class for a descriptor used to store an attribute that have values
    associated with Resolver objects.

    :param name: Attribute suffix used to store the property in the instance.
    :param placeholder_type: The type of placeholder that should be returned, when placeholders are
        allowed, when a resolver can't be resolved.
    """

    def __init__(self, name: str, placeholder_type=PlaceholderType.explicit):
        self.name = "_" + name
        self.logger = logging.getLogger(__name__)
        self.placeholder_type = placeholder_type

        self._lock = RLock()

    def __get__(self, stack: "stack.Stack", stack_class: Type["stack.Stack"]) -> Any:
        """
        Attribute getter which resolves the resolver(s).

        :param stack: The Stack instance the property is being retrieved for
        :param stack_class: The class of the stack that the property is being retrieved for.
        :return: The attribute stored with the suffix ``name`` in the instance.
        :rtype: The obtained value, as resolved by the property
        """
        with self._lock, self._no_recursive_get(stack):
            if hasattr(stack, self.name):
                return self.get_resolved_value(stack, stack_class)

    def __set__(self, stack: "stack.Stack", value: Any):
        """
        Attribute setter which adds a stack reference to any resolvers in the
        data structure `value` and calls the setup method.

        :param stack: The Stack instance the value is being set onto
        :param value: The value being set on the property
        """
        with self._lock:
            self.assign_value_to_stack(stack, value)

    @contextmanager
    def _no_recursive_get(self, stack: "stack.Stack"):
        # We don't care about recursive gets on the same property but different Stack instances,
        # only recursive gets on the same stack. Some Resolvers access the same property on OTHER
        # stacks and that actually shouldn't be a problem. Remember, these descriptor instances are
        # set on the CLASS and so instance variables on them are shared across all classes that
        # access them. Thus, we set this "get_in_progress" attribute on the stack instance rather
        # than the descriptor instance.
        get_status_name = f"_{self.name}_get_in_progress"
        if getattr(stack, get_status_name, False):
            raise RecursiveResolve(
                f"Resolving Stack.{self.name[1:]} required resolving itself"
            )
        setattr(stack, get_status_name, True)
        try:
            yield
        finally:
            setattr(stack, get_status_name, False)

    def get_setup_resolver_for_stack(
        self, stack: "stack.Stack", resolver: Resolver
    ) -> Resolver:
        """Obtains a clone of the resolver with the stack set on it and the setup method having
        been called on it.

        :param stack: The stack to set on the Resolver
        :param resolver: The Resolver to clone and set up
        :return: The cloned resolver.
        """
        # We clone the resolver when we assign the value so that every stack gets its own resolver
        # rather than potentially having one resolver instance shared in memory across multiple
        # stacks.
        clone = resolver.clone(stack)
        clone.setup()
        return clone

    @abc.abstractmethod
    def get_resolved_value(
        self, stack: "stack.Stack", stack_class: Type["stack.Stack"]
    ) -> Any:
        """Implement this method to return the value of the resolvable_property."""
        pass

    @abc.abstractmethod
    def assign_value_to_stack(self, stack: "stack.Stack", value: Any):
        """Implement this method to assign the value to the resolvable property."""
        pass

    def resolve_resolver_value(self, resolver: "Resolver") -> Any:
        """Returns the resolved parameter value.

        If the resolver happens to raise an error and placeholders are currently allowed for resolvers,
        a placeholder will be returned instead of reraising the error.

        :param resolver: The resolver to resolve.
        :return: The resolved value (or placeholder, in certain circumstances)
        """
        try:
            return resolver.resolve()
        except RecursiveResolve:
            # Recursive resolve issues shouldn't be masked by a placeholder.
            raise
        except Exception:
            if are_placeholders_enabled():
                placeholder_value = create_placeholder_value(
                    resolver, self.placeholder_type
                )

                self.logger.debug(
                    "Error encountered while resolving the resolver. This is allowed for the current "
                    f"operation. Resolving it to a placeholder value instead: {placeholder_value}"
                )
                return placeholder_value
            raise

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.name[1:]})>"


class ResolvableContainerProperty(ResolvableProperty):
    """
    This is a descriptor class used to store an attribute that may CONTAIN
    Resolver objects. Resolvers will be resolved upon access of this property.
    When resolvers are resolved, they will be replaced in the container with their
    resolved value, in order to avoid redundant resolutions.

    Supports nested dictionary and lists.

    :param name: Attribute suffix used to store the property in the instance.
    :type name: str
    """

    def __get__(
        self, stack: "stack.Stack", stack_class: Type["stack.Stack"]
    ) -> T_Container:
        container = super().__get__(stack, stack_class)

        with self._lock:
            # Resolve any deferred resolvers, now that the recursive get lock has been released.
            self._resolve_deferred_resolvers(stack, container)

        return container

    def get_resolved_value(
        self, stack: "stack.Stack", stack_class: Type["stack.Stack"]
    ) -> T_Container:
        """Obtains the resolved value for this property. Any resolvers that resolve to None will have
        their key/index removed from their dict/list where they are. Other resolvers will have their
        key/index's value replace with the resolved value to avoid redundant resolutions.

        :param stack: The Stack instance to obtain the value for
        :param stack_class: The class of the Stack instance.
        :return: The fully resolved container.
        """
        keys_to_delete = []

        def resolve(attr: Union[dict, list], key: Union[int, str], value: Resolver):
            # Update the container key's value with the resolved value, if possible...
            try:
                result = self.resolve_resolver_value(value)
                if result is None:
                    self.logger.debug(
                        f"Removing item {key} because resolver returned None."
                    )
                    # We gather up resolvers (and their immediate containers) that resolve to None,
                    # since that really means the resolver resolves to nothing. This is not common,
                    # but should be supported. We gather these rather than immediately remove them
                    # because this function is called in the context of looping over that attr, so
                    # we cannot alter its size until after the loop is complete.
                    keys_to_delete.append((attr, key))
                else:
                    attr[key] = result
            except RecursiveResolve:
                # It's possible that resolving the resolver might attempt to access another
                # resolvable property's value in this same container. In this case, we'll delay
                # resolution and instead return a ResolveLater so the value can be resolved outside
                # this recursion.
                attr[key] = self.ResolveLater(
                    stack,
                    self.name,
                    key,
                    lambda: value.resolve(),
                )

        container = getattr(stack, self.name)
        _call_func_on_values(resolve, container, Resolver)
        # Remove keys and indexes from their containers that had resolvers resolve to None.
        list_items_to_delete = []
        for attr, key in keys_to_delete:
            if isinstance(attr, list):
                # If it's a list, we want to gather up the items to remove from the list.
                # We don't want to modify the list length yet.
                # Since removals will change all the other list indexes,
                # we don't wan't to modify lists yet.
                list_items_to_delete.append((attr, attr[key]))
            else:
                del attr[key]

        for containing_list, item in list_items_to_delete:
            containing_list.remove(item)

        return container

    def assign_value_to_stack(self, stack: "stack.Stack", value: Union[dict, list]):
        """Assigns a COPY of the specified value to the stack instance. This method copies the value
        rather than directly assigns it to avoid bugs related to shared objects in memory.

        :param stack: The stack to assign the value to
        :param value: The value to assign
        """
        cloned = self._clone_container_with_resolvers(value, stack)
        setattr(stack, self.name, cloned)

    def _clone_container_with_resolvers(
        self, container: T_Container, stack: "stack.Stack"
    ) -> T_Container:
        """Recurses into the container, cloning and setting up resolvers and creating a copy of all
        nested containers.

        :param container: The container being recursed into and cloned
        :param stack: The stack the container is being copied for
        :return: The fully copied container with resolvers fully set up.
        """

        def recurse(obj):
            if isinstance(obj, Resolver):
                return self.get_setup_resolver_for_stack(stack, obj)
            if isinstance(obj, list):
                return [recurse(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: recurse(val) for key, val in obj.items()}
            return obj

        return recurse(container)

    def _resolve_deferred_resolvers(self, stack: "stack.Stack", container: T_Container):
        def raise_if_not_resolved(attr, key, value):
            # If this function has been hit, it means that after attempting to resolve all the
            # ResolveLaters, there STILL are ResolveLaters left in the container. Rather than
            # continuing to try to resolve (possibly infinitely), we'll raise a RecursiveGet to
            # break that infinite loop. This situation would happen if a resolver accesses a resolver
            # in the same container, which then accesses another resolver (possibly the same one) in
            # the same container.
            raise RecursiveResolve(
                f"Resolving Stack.{self.name[1:]} required resolving itself"
            )

        has_been_resolved_attr_name = f"{self.name}_is_resolved"
        if not getattr(stack, has_been_resolved_attr_name, False):
            # We set it first rather than after to avoid entering this block again on this property
            # for this stack.
            setattr(stack, has_been_resolved_attr_name, True)
            _call_func_on_values(
                lambda attr, key, value: value(), container, self.ResolveLater
            )
            # Search the container to see if there are any ResolveLaters left;
            # Raise a RecursiveResolve if there are.
            _call_func_on_values(raise_if_not_resolved, container, self.ResolveLater)

    class ResolveLater:
        """Represents a value that could not yet be resolved but can be resolved in the future."""

        def __init__(self, instance, name, key, resolution_function):
            self._instance = instance
            self._name = name
            self._key = key
            self._resolution_function = resolution_function

        def __call__(self):
            """Resolve the value."""
            attr = getattr(self._instance, self._name)
            result = self._resolution_function()
            if result is None:
                self.logger.debug(
                    f"Removing item {self._key} because resolver returned None."
                )
                del attr[self._key]
            else:
                attr[self._key] = result


class ResolvableValueProperty(ResolvableProperty):
    """
    This is a descriptor class used to store an attribute that may BE a single
    Resolver object. If it is a resolver, it will be resolved upon access of this property.
    When resolved, the resolved value will replace the resolver on the stack in order to avoid
    redundant resolutions.

    :param name: Attribute suffix used to store the property in the instance.
    :type name: str
    """

    def get_resolved_value(
        self, stack: "stack.Stack", stack_class: Type["stack.Stack"]
    ) -> Any:
        """Gets the fully-resolved value from the property. Resolvers will be replaced on the stack
        instance with their resolved value to avoid redundant resolutions.

        :param stack: The Stack instance to obtain the value from
        :param stack_class: The class of the Stack instance
        :return: The fully resolved value
        """
        raw_value = getattr(stack, self.name)
        if isinstance(raw_value, Resolver):
            value = self.resolve_resolver_value(raw_value)
            # Overwrite the stored resolver value with the resolved value to avoid resolving the
            # same value multiple times.
            setattr(stack, self.name, value)
        else:
            value = raw_value

        return value

    def assign_value_to_stack(self, stack: "stack.Stack", value: Any):
        """Assigns the value to the Stack instance passed, setting up and cloning the value if it
        is a Resolver.

        :param stack: The Stack instance to set the value on
        :param value: The value to set
        """
        if isinstance(value, Resolver):
            value = self.get_setup_resolver_for_stack(stack, value)
        setattr(stack, self.name, value)
