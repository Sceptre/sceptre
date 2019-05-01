# -*- coding: utf-8 -*-
import abc
import six
import logging

from sceptre.helpers import _call_func_on_values


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

    def __get__(self, instance, type):
        """
        Attribute getter which resolves any Resolver object contained in the
        complex data structure.

        :return: The attribute stored with the suffix ``name`` in the instance.
        :rtype: dict or list
        """
        def resolve(attr, key, value):
            attr[key] = value.resolve()

        if hasattr(instance, self.name):
            return _call_func_on_values(
                resolve, getattr(instance, self.name), Resolver
            )

    def __set__(self, instance, value):
        """
        Attribute setter which adds a stack reference to any resolvers in the
        data structure `value` and calls the setup method.

        """
        def setup(attr, key, value):
            value.stack = instance
            value.setup()

        _call_func_on_values(setup, value, Resolver)
        setattr(instance, self.name, value)
