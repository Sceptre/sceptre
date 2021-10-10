# -*- coding: utf-8 -*-
import abc
import logging
from contextlib import contextmanager
from threading import RLock
from typing import Any

from sceptre.helpers import _call_func_on_values


class RecursiveResolve(Exception):
    pass


class Resolver(abc.ABC):
    """
    Resolver is an abstract base class that should be inherited by all
    Resolvers.

    :param argument: The argument of the resolver.
    :type argument: str
    :param stack: The associated stack of the resolver.
    :type stack: sceptre.stack.Stack
    """

    def __init__(self, argument=None, stack=None):
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

    def clone(self, stack=None):
        """
        Produces a "fresh", pre-setup copy of the Resolver, with the specified stack.

        :param stack: The stack to set on the cloned resolver
        :type stack: sceptre.stack.Stack
        """
        return type(self)(self.argument, stack)


class ResolvableProperty(abc.ABC):
    """
    This is an abstract base class for a descriptor used to store an attribute that have values
    associated with Resolver objects.

    :param name: Attribute suffix used to store the property in the instance.
    :type name: str
    """

    def __init__(self, name):
        self.name = "_" + name
        self.logger = logging.getLogger(__name__)
        self._get_in_progress = False
        self._lock = RLock()

    def __get__(self, stack, type):
        """
        Attribute getter which resolves the resolver(s).

        :return: The attribute stored with the suffix ``name`` in the instance.
        :rtype: dict or list
        """
        with self._lock, self._no_recursive_get():
            if hasattr(stack, self.name):
                return self.get_resolved_value(stack, type)

    def __set__(self, stack, value):
        """
        Attribute setter which adds a stack reference to any resolvers in the
        data structure `value` and calls the setup method.
        """
        with self._lock:
            self.assign_value_to_stack(stack, value)

    @contextmanager
    def _no_recursive_get(self):
        if self._get_in_progress:
            raise RecursiveResolve(f"Resolving Stack.{self.name} required resolving Stack.{self.name}")
        self._get_in_progress = True
        try:
            yield
        finally:
            self._get_in_progress = False

    @abc.abstractmethod
    def get_resolved_value(self, stack, type) -> Any:
        """Implement this method to return the value of the resolvable_property."""
        pass

    @abc.abstractmethod
    def assign_value_to_stack(self, stack, value: Any):
        """Implement this method to assign the value to the resolvable property."""
        pass


class ResolvableContainerProperty(ResolvableProperty):
    """
    This is a descriptor class used to store an attribute that may contain
    Resolver objects. When retrieving the dictionary or list, any Resolver
    objects contains are a value or within a list are resolved to a primitive
    type. Supports nested dictionary and lists.

    :param name: Attribute suffix used to store the property in the instance.
    :type name: str
    """
    def __init__(self, name):
        super().__init__(name)
        self._deferred_resolution_has_been_triggered = False

    def __get__(self, stack, type):
        container = super().__get__(stack, type)

        with self._lock:
            if not self._deferred_resolution_has_been_triggered:
                # Resolve any deferred resolvers, now that the recursive lock has been released.
                self.resolve_deferred_resolvers(container)

        return container

    def get_resolved_value(self, stack, type):
        def resolve(attr, key, value):
            # Update the container key's value with the resolved value, if possible...
            try:
                attr[key] = value.resolve()
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
        _call_func_on_values(
            resolve, container, Resolver
        )
        return container

    def assign_value_to_stack(self, stack, value):
        cloned = self._clone_resolvers_recursively(value, stack)
        setattr(stack, self.name, cloned)

    def _clone_resolvers_recursively(self, value, stack):
        if isinstance(value, Resolver):
            # We clone the resolver to avoid the case where the SAME resolver defined on a
            # StackGroup gets shared on multiple stacks because the stack on that shared resolver
            # would be updated to whatever the last stack it was set to, which could lead to weird
            # bugs. By cloning the stack, we guarantee each stack gets its own copy of the resolver.
            value = value.clone(stack)
            value.setup()
            return value
        if isinstance(value, list):
            return [self._clone_resolvers_recursively(item, stack) for item in value]
        elif isinstance(value, dict):
            return {
                key: self._clone_resolvers_recursively(val, stack)
                for key, val in value.items()
            }
        return value

    def resolve_deferred_resolvers(self, container):
        self._deferred_resolution_has_been_triggered = True
        _call_func_on_values(
            lambda attr, key, value: value(),
            container,
            self.ResolveLater
        )

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
            attr[self._key] = self._resolution_function()


class ResolvableValueProperty(ResolvableProperty):

    def get_resolved_value(self, stack, type):
        raw_value = getattr(stack, self.name)
        if isinstance(raw_value, Resolver):
            value = raw_value.resolve()
            # Overwrite the stored resolver value with the resolved value to avoid resolving the
            # same value multiple times.
            setattr(stack, self.name, value)
        else:
            value = raw_value

        return value

    def assign_value_to_stack(self, stack, value):
        if isinstance(value, Resolver):
            # We clone the resolver when we assign the value so that every stack gets its own resolver
            # rather than potentially having one resolver instance shared in memory across multiple
            # stacks.
            value = value.clone(stack)
            value.setup()
        setattr(stack, self.name, value)
