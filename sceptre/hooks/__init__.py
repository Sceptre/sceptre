import abc
import logging
from functools import wraps
from typing import TYPE_CHECKING, List

from sceptre.helpers import _call_func_on_values
from sceptre.resolvers import CustomYamlTagBase

if TYPE_CHECKING:
    from sceptre.stack import Stack


class Hook(CustomYamlTagBase, metaclass=abc.ABCMeta):
    """
    Hook is an abstract base class that should be subclassed by all hooks.
    """

    logger = logging.getLogger(__name__)

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

    def __set__(self, instance: "Stack", value):
        """
        Attribute setter which adds a stack reference to any hooks in the
        data structure `value` and calls the setup method.

        """

        def setup(attr, key, value: Hook):
            attr[key] = clone = value.clone_for_stack(instance)
            clone.setup()

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


def add_stack_hooks_with_aliases(function_aliases: List[str]):
    """
    Returns a decorator to trigger the before and after hooks, relative to the decorated function's
    name AS WELL AS the passed function alias names.
    :param function_aliases: The list of OTHER functions to trigger hooks around.
    :return: The hook-triggering decorator.
    """

    def decorator(func):
        all_hook_names = [func.__name__] + function_aliases

        @wraps(func)
        def decorated(self, *args, **kwargs):
            for hook in all_hook_names:
                before_hook_name = f"before_{hook}"
                execute_hooks(self.stack.hooks.get(before_hook_name))

            response = func(self, *args, **kwargs)

            for hook in all_hook_names:
                after_hook_name = f"after_{hook}"
                execute_hooks(self.stack.hooks.get(after_hook_name))

            return response

        return decorated

    return decorator
