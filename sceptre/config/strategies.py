# -*- coding: utf-8 -*-

"""
sceptre.config.strategies

This module contains the implementations of the strategies used to merge config
attributes.
"""
from copy import deepcopy


def list_join(a, b):
    """
    Takes two lists and joins them.

    :param a: A list.
    :type a: list
    :param b: A list.
    :type b: list
    :returns: A joined list from the two parameters.
    :rtype: list
    """
    if a and not isinstance(a, list):
        raise TypeError("{} is not a list".format(a))

    if b and not isinstance(b, list):
        raise TypeError("{} is not a list".format(b))

    if a is None:
        return deepcopy(b)

    if b is not None:
        return deepcopy(a + b)

    return deepcopy(a)


def dict_merge(a, b):
    """
    Takes two dictionaries and merges them.

    :param a: A dictionary.
    :type a: dict
    :param b: A dictionary.
    :type b: dict
    :returns: A merged dict.
    :rtype: dict
    """
    if a and not isinstance(a, dict):
        raise TypeError("{} is not a dict".format(a))
    if b and not isinstance(b, dict):
        raise TypeError("{} is not a dict".format(b))

    if a is None:
        return deepcopy(b)

    if b is not None:
        return deepcopy({**a, **b})

    return deepcopy(a)


def child_wins(a, b):
    """
    Always returns the second parameter.

    :param a: An object.
    :type a: object
    :param b: An object.
    :type b: object
    :returns: b
    """
    return b


def child_or_parent(a, b):
    """
    Returns the second arg if it is not empty, else the first.

    :param a: An object.
    :type a: object
    :param b: An object.
    :type b: object
    :returns: b
    """
    return b or a


LIST_STRATEGIES = {
    "merge": list_join,
    "override": child_wins,
}
DICT_STRATEGIES = {
    "merge": dict_merge,
    "override": child_wins,
}
