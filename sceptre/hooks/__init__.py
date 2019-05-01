import abc
import logging
from functools import wraps

from sceptre.helpers import _call_func_on_values


class Hook(object):
    """
    Hook is an abstract base class that should be inherited by all hooks.

    :param argument: The argument of the hook.
    :type argument: str
    :param stack: The associated stack of the hook.
    :type stack: sceptre.stack.Stack
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, argument=None, stack=None):
        self.logger = logging.getLogger(__name__)
        self.argument = argument
        self.stack = stack

    def setup(self):
        """
        setup is a method that may be overwritten by inheriting classes. Allows
        hooks to run so initalisation steps when config is first read.
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def run(self):
        """
        run is an abstract method which must be overwritten by all
        inheriting classes. Run should execute the logic of the hook.
        """
        pass  # pragma: no cover


class HookProperty(object):
    """
    This is a descriptor class used to store an attribute that may contain
    Hook objects. Used to setup Hooks when added as a attribute. Supports
    nested dictionary and lists.

    :param name: Attribute suffix used to store the property in the instance.
    :type name: str
    """

    def __init__(self, name):
        self.name = "_" + name
        self.logger = logging.getLogger(__name__)

    def __get__(self, instance, type):
        """
        Attribute getter for Hook containing data structure.

        :return: The attribute stored with the suffix ``name`` in the instance.
        :rtype: dict or list
        """
        return getattr(instance, self.name)

    def __set__(self, instance, value):
        """
        Attribute setter which adds a stack reference to any hooks in the
        data structure `value` and calls the setup method.

        """
        def setup(attr, key, value):
            value.stack = instance
            value.setup()

        _call_func_on_values(setup, value, Hook)
        setattr(instance, self.name, value)


def execute_hooks(hooks):
    """
    Searches through dictionary or list for Resolver objects and replaces
    them with the resolved value. Supports nested dictionaries and lists.
    Does not detect Resolver objects used as keys in dictionaries.

    :param attr: A complex data structure to search through.
    :type attr: dict or list
    :return: A complex data structure without Resolver objects.
    :rtype: dict or list
    """
    if isinstance(hooks, list):
        for hook in hooks:
            if isinstance(hook, Hook):
                hook.run()


def add_stack_hooks(func):
    """
    A function decorator to trigger the before and after hooks, relative
    to the decorated function's name.
    :param func: a function that operates on a stack
    :type func: function
    """
    @wraps(func)
    def decorated(self, *args, **kwargs):
        execute_hooks(self.stack.hooks.get("before_" + func.__name__))
        response = func(self, *args, **kwargs)
        execute_hooks(self.stack.hooks.get("after_" + func.__name__))

        return response

    return decorated
