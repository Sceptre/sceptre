import abc
import logging
from functools import wraps


class Hook(object):
    """
    Hook is an abstract base class that should be inherited by all
    hooks used in hooks. Environment and stack config and the connection
    manager are supplied to the class, as they may be of use to inheriting
    classes.

    :param argument: The argument in which the task can use.
    :type argument: str
    :param environment_config: The environment_config from config.yaml files.
    :type environment_config: sceptre.config.Config
    :param stack_config: The stack config of the stack that this parameter is \
    associated with.
    :type stack_config: sceptre.config.Config
    :param connection_manager: A connection_manager.
    :type connection_manager: sceptre.connection_manager.ConnectionManager
    """
    __metaclass__ = abc.ABCMeta

    def __init__(
            self, argument=None, connection_manager=None,
            environment_config=None, stack_config=None):
        self.logger = logging.getLogger(__name__)
        self.argument = argument
        self.connection_manager = connection_manager
        self.environment_config = environment_config
        self.stack_config = stack_config

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
