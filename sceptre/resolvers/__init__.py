# -*- coding: utf-8 -*-
import abc
import logging
from contextlib import contextmanager
from threading import RLock

import six
from sceptre.helpers import _call_func_on_values


class RecursiveGet(Exception):
    pass


@six.add_metaclass(abc.ABCMeta)
class Resolver:
    """
    Resolver is an abstract base class that should be inherited by all
    Resolvers.

    :param argument: The argument of the resolver.
    :type argument: str
    :param stack: The associated stack of the resolver.
    :type stack: sceptre.stack.Stack
    """

    __metaclass__ = abc.ABCMeta

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


class ResolvableProperty(object):
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

    def __get__(self, instance, type):
        """
        Attribute getter which resolves any Resolver object contained in the
        complex data structure.

        :return: The attribute stored with the suffix ``name`` in the instance.
        :rtype: dict or list
        """
        with self._lock, self._no_recursive_get():
            def resolve(attr, key, value):
                try:
                    attr[key] = value.resolve()
                except RecursiveGet:
                    attr[key] = self.ResolveLater(instance, self.name, key,
                                                  lambda: value.resolve())

            if hasattr(instance, self.name):
                retval = _call_func_on_values(
                    resolve, getattr(instance, self.name), Resolver
                )
                return retval

    def __set__(self, instance, value):
        """
        Attribute setter which adds a stack reference to any resolvers in the
        data structure `value` and calls the setup method.

        """
        def setup(attr, key, value):
            value.stack = instance
            value.setup()

        with self._lock:
            _call_func_on_values(setup, value, Resolver)
            setattr(instance, self.name, value)

    class ResolveLater(object):
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

    @contextmanager
    def _no_recursive_get(self):
        if self._get_in_progress:
            raise RecursiveGet()
        self._get_in_progress = True
        try:
            yield
        finally:
            self._get_in_progress = False
