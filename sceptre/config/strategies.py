# -*- coding: utf-8 -*-

"""
sceptre.config.strategies

This module contains the implementations of the strategies used to merge config
attributes.
"""


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
        raise TypeError('{} is not a list'.format(a))
    if b and not isinstance(b, list):
        raise TypeError('{} is not a list'.format(b))

    if a is None:
        return b

    if b is not None:
        return a + b

    return a


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
        raise TypeError('{} is not a dict'.format(a))
    if b and not isinstance(b, dict):
        raise TypeError('{} is not a dict'.format(b))

    if a is None:
        return b

    if b is not None:
        a.update(b)
        return a

    return a


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
