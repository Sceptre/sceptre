# -*- coding: utf-8 -*-

import fnmatch
import glob
import imp
import inspect
import sys
import re
import yaml
import jinja2
from functools import wraps
from os import path, walk, environ

from copy import copy
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from .config.graph import StackDependencyGraph


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


def recurse_sub_stack_groups_with_graph(func):
    return recurse_into_sub_stack_groups(func, StackDependencyGraph)


def recurse_into_sub_stack_groups(func, factory=dict):
    """
    Two types of StackGroups exist, non-leaf and leaf. Non-leaf
    stack_groups contain sub-stack_groups, while leaf
    stack_groups contain stacks. If a command is executed by a leaf
    stack_group, it should execute that command on the stacks it
    contains. If a command is executed by a non-leaf stack_group, it
    should invoke that command on each of its sub-stack_groups. Recurse
    is a decorator used by sceptre.stack_group.StackGroup to do
    this. The function passed, ``func``, must return a dictionary.
    """
    @wraps(func)
    def decorated(self, *args, **kwargs):
        import ipdb
        ipdb.set_trace()
        function_name = func.__name__
        responses = factory()
        nkwargs = copy(kwargs)

        stack_group = kwargs.get('stack_group', self.stack_group)
        kwargs.update({'stack_group': stack_group})
        num_stack_groups = len(stack_group.sub_stack_groups)
        # As commands carried out by sub-stack_groups may be blocking,
        # execute them on separate threads.
        if num_stack_groups:
            with ThreadPoolExecutor(max_workers=num_stack_groups)\
                    as thread_stack_group:
                futures = []
                for stack_group in stack_group.sub_stack_groups:
                    nkwargs.update({'stack_group': stack_group})

                    futures.append(thread_stack_group.submit(
                        getattr(self, function_name), *args, **nkwargs
                    ))
                for future in as_completed(futures):
                    response = future.result()
                    if response:
                        responses.update(response)

        response = func(self, *args, **kwargs)
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

    A dependency stack's name can be provided as either a full stack name, or
    as the file base name of a stack from the same stack_group.
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


def generate_dependencies(stack_group):
    """
    Generates a full map of dependencies given either a Stack or StackGroup as
    a parameter. This includes dependencies that are external to the given
    Stack.

    :param stack_or_stack_group: A Stack or StackGroup
    :type stack_or_stack_group: str
    :returns: A map of every dependency required for the given Stack or
    StackGroup
    :rtype: dict
    """
    final_deps = {}
    abs_project_path = path.split(path.abspath(stack_or_stack_group))[0]
    templating_vars = {}
    sceptre_dir = get_sceptre_dir(abs_project_path)

    def recurse_deps(stack_group):
        stack_group = stack_group

        if path.isdir(path.join(sceptre_dir, stack_or_stack_group)):
            root = path.join(sceptre_dir, stack_or_stack_group)
        else:
            root = path.split(stack_or_stack_group)[0]

        for directory_name, sub_directories, files in walk(root):
            for filename in fnmatch.filter(files, '*.yaml'):
                if not filename.startswith("config"):
                    def get_dependencies(config_path):
                        abs_directory_path = path.abspath(directory_name)
                        if path.isfile(path.join(abs_directory_path, filename)):
                            stack_group = jinja2.Environment(
                                loader=jinja2.FileSystemLoader(
                                    abs_directory_path),
                                undefined=jinja2.StrictUndefined
                            )

                            template = stack_group.get_template(filename)
                            rendered_template = template.render(
                                environment_variable=environ,
                                stack_group_path=config_path,
                                **templating_vars
                            )

                            config = yaml.safe_load(rendered_template)
                            return config.get("dependencies", [])

                    dependencies = get_dependencies(directory_name)
                    final_deps.update({
                        # trim extension
                        get_stack_group_name(directory_name) + '/' + filename[:-5]: dependencies
                    })
                    for d in dependencies:
                        recurse_deps(path.split(d)[0])

    recurse_deps(stack_group)
    return final_deps


def generate_stack_groups(stack_or_stack_group):
    """
    Generates a full list of stack groups given either a Stack or StackGroup as
    a parameter. This includes dependencies that are external to the given
    Stack.

    :param stack_or_stack_group: A Stack or StackGroup
    :type stack_or_stack_group: str
    :returns: A list of every stack group for the given Stack or StackGroup
    :rtype: list
    """
    stack_groups = {}
    abs_project_path = path.split(path.abspath(stack_or_stack_group))[0]
    templating_vars = {}
    sceptre_dir = get_sceptre_dir(abs_project_path)

    def recurse_deps(stack_or_stack_group):
        stack_or_stack_group = stack_or_stack_group

        if path.isdir(path.join(sceptre_dir, stack_or_stack_group)):
            root = path.join(sceptre_dir, stack_or_stack_group)
        else:
            root = path.split(stack_or_stack_group)[0]

        for directory_name, sub_directories, files in walk(root):
            for filename in fnmatch.filter(files, '*.yaml'):
                if not filename.startswith("config"):
                    def get_dependencies(config_path):
                        abs_directory_path = path.abspath(directory_name)
                        if path.isfile(path.join(abs_directory_path, filename)):
                            stack_group = jinja2.Environment(
                                loader=jinja2.FileSystemLoader(
                                    abs_directory_path),
                                undefined=jinja2.StrictUndefined
                            )

                            template = stack_group.get_template(filename)
                            rendered_template = template.render(
                                environment_variable=environ,
                                stack_group_path=config_path,
                                **templating_vars
                            )

                            config = yaml.safe_load(rendered_template)
                            return config.get("dependencies", [])

                    dependencies = get_dependencies(directory_name)
                    stack_groups.update({
                        get_stack_group_name(directory_name): dependencies
                    })
                    for d in dependencies:
                        recurse_deps(path.split(d)[0])

    recurse_deps(stack_or_stack_group)
    return stack_groups


def read_config(config_path, templating_vars):
    if path.isfile(config_path):
        stack_group = jinja2.Environment(
            loader=jinja2.FileSystemLoader(config_path),
            undefined=jinja2.StrictUndefined
        )

        template = stack_group.get_template(path.split(config_path)[1])
        rendered_template = template.render(
            environment_variable=environ,
            stack_group_path=config_path,
            **templating_vars
        )

        config = yaml.safe_load(rendered_template)
        return config


def get_sceptre_dir(abs_path):
    for dir_name, sub_dir, files in walk(abs_path, topdown=False):
        if path.join(abs_path, dir_name).endswith('config'):
            return path.abspath(dir_name)


def get_stack_group_name(abs_path):
    temp_path = abs_path
    final_path = ""

    while path.split(temp_path)[1] != 'config':
        final_path = path.join(path.split(temp_path)[1], final_path)
        temp_path = path.split(temp_path)[0]

    return final_path[:-1]  # remove trailing slash


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
        glob_expression = path.join(directory, "*.py")
    except (AttributeError, TypeError):
        raise TypeError("'directory' object should be a string")

    module_paths = glob.glob(glob_expression)

    sys.path.append(directory)

    modules = [
        imp.load_source(
            path.basename(module_path).split(".")[0], module_path
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


def _call_func_on_values(func, attr, cls):
    """
    Searches through dictionary or list for objects of type `cls` and calls the
    supplied function `func`. Supports nested dictionaries and lists.
    Does not detect objects used as keys in dictionaries.

    :param attr: A dictionary or list to search through.
    :type attr: dict or list
    :return: The dictionary or list structure.
    :rtype: dict or list
    """

    def func_on_instance(key):
        if isinstance(value, cls):
            func(attr, key, value)
        elif isinstance(value, list) or isinstance(value, dict):
            _call_func_on_values(func, value, cls)

    if isinstance(attr, dict):
        for key, value in attr.items():
            func_on_instance(key)
    elif isinstance(attr, list):
        for index, value in enumerate(attr):
            func_on_instance(index)
    return attr
