# -*- coding: utf-8 -*-
from contextlib import contextmanager
from datetime import datetime
from os import sep
from typing import Optional, Any, List

import dateutil.parser

from sceptre.exceptions import PathConversionError


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
    return "-".join([project_code, stack_name.replace("/", "-")])


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

    return "".join(["*" if i < num_mask_chars else c for i, c in enumerate(key)])


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


def normalise_path(path):
    """
    Converts a path to use correct path separator.
    Raises an PathConversionError if the path has a
    trailing slash.
    :param path: A directory path
    :type path: str
    :raises: sceptre.exceptions.PathConversionError
    :returns: A normalised path with forward slashes.
    :returns: string
    """
    if sep == "/":
        path = path.replace("\\", "/")
    elif sep == "\\":
        path = path.replace("/", "\\")
    if path.endswith("/") or path.endswith("\\"):
        raise PathConversionError(
            "'{0}' is an invalid path string. Paths should "
            "not have trailing slashes.".format(path)
        )
    return path


def sceptreise_path(path):
    """
    Converts a path to use correct sceptre path separator.
    Raises an PathConversionError if the path has a
    trailing slash.
    :param path: A directory path
    :type path: str
    :raises: sceptre.exceptions.PathConversionError
    :returns: A normalised path with forward slashes.
    :returns: string
    """
    path = path.replace("\\", "/")
    if path.endswith("/") or path.endswith("\\"):
        raise PathConversionError(
            "'{0}' is an invalid path string. Paths should "
            "not have trailing slashes.".format(path)
        )
    return path


@contextmanager
def null_context():
    """A context manager that does nothing. This is identical to the nullcontext in py3.7+, but isn't
    available in py3.6, so providing it here instead.
    """
    yield


def extract_datetime_from_aws_response_headers(
    boto_response: dict,
) -> Optional[datetime]:
    """Returns a datetime.datetime extracted from the response metadata in a
    boto response or None if it's unable to find or parse one.
    :param boto_response: A dictionary returned from a boto client call
    :returns a datetime.datetime or None
    """
    if boto_response is None:
        return None
    try:
        return dateutil.parser.parse(
            boto_response["ResponseMetadata"]["HTTPHeaders"]["date"]
        )
    except (KeyError, dateutil.parser.ParserError):
        # We expect a KeyError if the date isn't present in the response. We
        # expect a ParserError if it's not well-formed. Any other error we want
        # to pass along.
        return None


def gen_repr(instance: Any, class_label: str = None, attributes: List[str] = []) -> str:
    """
    Returns a standard __repr__ based on instance attributes.
    :param instance: The instance to represent (`self`).
    :param class_label: Override the name of the class found through introspection.
    :param attributes: List the attributes to include the in representation.
    :returns: A string representation of `instance`
    """
    if not class_label:
        class_label = instance.__class__.__name__
    attr_str = ", ".join(
        [f"{a}={repr(instance.__getattribute__(a))}" for a in attributes]
    )
    return f"{class_label}({attr_str})"
