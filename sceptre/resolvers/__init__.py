# -*- coding: utf-8 -*-
import abc
import logging


class Resolver(object):
    """
    Resolver is an abstract base class that should be inherited by all
    resolvers. Environment config, stack config and the connection
    manager are supplied to the class, as they may be of use to inheriting
    classes.

    :param environment_config: The environment_config from config.yaml files.
    :type environment_config: sceptre.config.Config
    :param stack_config: The stack config.
    :type stack_config: sceptre.config.Config
    :param connection_manager: A connection manager.
    :type connection_manager: sceptre.connection_manager.ConnectionManager
    :param argument: Arguments to pass to the resolver.
    :type argument: str
    """

    __metaclass__ = abc.ABCMeta

    def __init__(
        self, argument=None, connection_manager=None,
        environment_config=None, stack_config=None
    ):
        self.logger = logging.getLogger(__name__)
        self.environment_config = environment_config
        self.stack_config = stack_config
        self.connection_manager = connection_manager
        self.argument = argument

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
    :type name: string
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
        if not hasattr(instance, self.name) \
                or getattr(instance, self.name) is None:
            value = instance.config.get(self.name[1:], {})
            setattr(instance, self.name, value)
        return self.resolve_values(getattr(instance, self.name))

    def __set__(self, instance, value):
        setattr(instance, self.name, value)

    def resolve_values(self, attr):
        """
        Searches through dictionary or list for Resolver objects and replaces
        them with the resolved value. Supports nested dictionaries and lists.
        Does not detect Resolver objects used as keys in dictionaries.

        :param attr: A complex data structure to search through.
        :type attr: dict or list
        :return: A complex data structure without Resolver objects.
        :rtype: dict or list
        """
        if isinstance(attr, dict):
            for key, value in attr.items():
                if isinstance(value, Resolver):
                    attr[key] = value.resolve()
                elif isinstance(value, list) or isinstance(value, dict):
                    self.resolve_values(value)
        elif isinstance(attr, list):
            for index, value in enumerate(attr):
                if isinstance(value, Resolver):
                    attr[index] = value.resolve()
                elif isinstance(value, list) or isinstance(value, dict):
                    self.resolve_values(value)
        return attr
