# -*- coding: utf-8 -*-

from functools import wraps
import glob
import imp
import inspect
import os
import re
import sys

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed


def camel_to_snake_case(string):
    """
    Converts a string from camel case to snake case.

    :param string: The string to be converted from camel to snake case.
    :type string: str
    :returns: The string, in snake case.
    :rtype: str
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def recurse_into_sub_environments(func):
    """
    Two types of Environments exist, non-leaf and leaf. Non-leaf environments
    contain sub-environments, while leaf environments contain stacks. If a
    command is executed by a leaf environment, it should execute that command
    on the stacks it contains. If a command is executed by a non-leaf
    environment, it should invoke that command on each of its sub-environments.
    recurse is a decorator used by sceptre.environment.Environment to do this.
    The function passed, ``func``, must return a dictionary.
    """
    @wraps(func)
    def decorated(self, *args, **kwargs):
        if self.is_leaf:
            return func(self, *args, **kwargs)
        else:
            function_name = func.__name__
            responses = {}
            num_environments = len(self.environments)

            # As commands carried out by sub-environments may be blocking,
            # execute them on separate threads.
            with ThreadPoolExecutor(max_workers=num_environments) as executor:
                futures = [
                    executor.submit(
                        getattr(environment, function_name), *args, **kwargs
                    )
                    for environment in self.environments.values()
                ]
                for future in as_completed(futures):
                    response = future.result()
                    if response:
                        responses.update(response)
            return responses

    return decorated


def get_name_tuple(name):
    """
    Returns a tuple of the stack name, split on the slashes.

    :param name: The Stack's name.
    :type name: str
    :returns: A tuple of the stack's name.
    :rtype: tuple
    """
    return tuple(name.split("/"))


def resolve_stack_name(source_stack_name, destination_stack_path):
    """
    Returns a stack's full name.

    A dependancy stack's name can be provided as either a full stack name, or
    as the file base name of a stack from the same environment.
    resolve_stack_name calculates the dependency's stack's full name from this.

    :param source_stack_name: The name of the stack with the parameter to be \
    resolved.
    :type source_stack_name: str
    :param destination_stack_path: The full or short name of the depenency \
    stack.
    :type destination_stack_path: str
    :returns: The stack's full name.
    :rtype: str
    """
    if "/" in destination_stack_path:
        return destination_stack_path
    else:
        source_stack_base_name = source_stack_name.rsplit("/", 1)[0]
        return "/".join([source_stack_base_name, destination_stack_path])


def get_external_stack_name(project_code, stack_name):
    """
    Returns the name given to a stack in CloudFormation.

    :param project_code: The project code, as defined in config.yaml.
    :type project_code: str
    :param stack_name: The name of the stack.
    :type stack_name: str
    :returns: The name given to the stack in CloudFormation.
    :rtype: str
    """
    return "-".join([
        project_code,
        stack_name.replace("/", "-")
    ])


def mask_key(key):
    """
    Returns an masked version of ``key``.

    Returned version has all but the last four characters are replaced with the
    character "*".

    :param key: The string to mask.
    :type key: str
    :returns: An masked version of the key
    :rtype: str
    """
    num_mask_chars = len(key) - 4

    return "".join([
        "*" if i < num_mask_chars else c
        for i, c in enumerate(key)
    ])


def get_subclasses(class_type, directory=None):
    """
    Creates a dictionary of classes which inherit from ``class_type`` found in
    all python files within a given directory, keyed by the class name in snake
    case as a string.

    :param class_type: The base class that all returned classes should inherit
        from.
    :type class_type: cls
    :param directory: The directory to look for classes in.
    :type directory: str
    :returns: A dict of classes found.
    :rtype: dict
    """
    try:
        glob_expression = os.path.join(directory, "*.py")
    except (AttributeError, TypeError):
        raise TypeError("'directory' object should be a string")

    module_paths = glob.glob(glob_expression)

    sys.path.append(directory)

    modules = [
        imp.load_source(
            os.path.basename(module_path).split(".")[0], module_path
        )
        for module_path in module_paths
        if "__init__" not in module_path
    ]

    classes = {}

    for module in modules:
        for attr in module.__dict__.values():
            if inspect.isclass(attr) \
                and issubclass(attr, class_type) \
                    and not inspect.isabstract(attr):
                        classes[camel_to_snake_case(attr.__name__)] = attr

    return classes
