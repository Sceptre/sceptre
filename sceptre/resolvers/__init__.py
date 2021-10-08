# -*- coding: utf-8 -*-
import abc
import logging
from contextlib import contextmanager
from threading import RLock

from sceptre.helpers import _call_func_on_values


class RecursiveGet(Exception):
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
        Produces a "fresh", pre-setup copy of the Resolver, with the sta

        :param stack: The stack to set on the cloned resolver
        :type stack: sceptre.stack.Stack
        """
        return type(self)(self.argument, stack)


class ResolveLater:
    """Represents a value that could not yet be resolved but can be resolved in the future."""

    def __init__(self, instance, name, resolution_function):
        self._instance = instance
        self._name = name
        self._resolution_function = resolution_function

    @property
    def attribute(self):
        return getattr(self._instance, self._name)

    @attribute.setter
    def attribute(self, value):
        setattr(self._instance, self._name, value)

    def __call__(self):
        self.attribute = self._resolution_function


class ResolvableProperty:
    """
    This is a descriptor class used to store an attribute that may contain
    Resolver objects. When retrieving the dictionary or list, any Resolver
    objects contains are a value or within a list are resolved to a primitive
    type. Supports nested dictionary and lists.

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
        Attribute getter which resolves any Resolver object contained in the
        complex data structure.

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
            raise RecursiveGet()
        self._get_in_progress = True
        try:
            yield
        finally:
            self._get_in_progress = False

    @abc.abstractmethod
    def get_resolved_value(self, stack, type):
        pass

    @abc.abstractmethod
    def assign_value_to_stack(self, stack, value):
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

    def get_resolved_value(self, instance, type):
        def resolve(attr, key, value):
            try:
                attr[key] = value.resolve()
            except RecursiveGet:
                attr[key] = self.ResolveContainerLater(
                    instance,
                    self.name,
                    lambda: value.resolve(),
                    key,
                )

        container = getattr(instance, self.name)
        _call_func_on_values(
            resolve, container, Resolver
        )
        return container

    def assign_value_to_stack(self, stack, value):
        cloned = self._clone_resolvers_recursively(value, stack)
        setattr(stack, self.name, cloned)

    def _clone_resolvers_recursively(self, value, stack):
        if isinstance(value, Resolver):
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

    class ResolveContainerLater(ResolveLater):
        """Represents a value that could not yet be resolved but can be resolved in the future."""

        def __init__(self, instance, name, resolution_function, key):
            super().__init__(instance, name, resolution_function)
            self._key = key

        def __call__(self):
            """Resolve the value."""
            self.attribute[self._key] = self._resolution_function()


class ResolvableValueProperty(ResolvableProperty):
    def get_resolved_value(self, stack, type):
        raw_value = getattr(stack, self.name)
        if isinstance(raw_value, Resolver):
            value = self._resolve(raw_value)
            setattr(stack, self.name, value)
        else:
            value = raw_value
        return value

    def _resolve(self, resolver):
        try:
            return resolver.resolve()
        except RecursiveGet:
            return ResolveLater(
                resolver,
                self.name,
                lambda: resolver.resolve()
            )

    def assign_value_to_stack(self, stack, value):
        if isinstance(value, Resolver):
            value = value.clone(stack)
            value.setup()
        setattr(stack, self.name, value)
