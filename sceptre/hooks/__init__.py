import abc
import logging
from functools import wraps


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

    @abc.abstractmethod
    def run(self):
        """
        run is an abstract method which must be overwritten by all
        inheriting classes. Run should execute the logic of the hook.
        """
        pass  # pragma: no cover


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
        execute_hooks(self.hooks.get("before_" + func.__name__))
        response = func(self, *args, **kwargs)
        execute_hooks(self.hooks.get("after_" + func.__name__))

        return response

    return decorated
