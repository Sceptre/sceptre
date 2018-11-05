# -*- coding: utf-8 -*-

"""
sceptre.stack_group

This module implements the StackGroup class, which stores data and logic
to represent a logical grouping of stacks as a stack_group.

"""

import logging


class StackGroup(object):
    """
    StackGroup stores information about the current stack_group.

    It implements methods for carrying out stack_group-level operations.

    Two types of StackGroups exist, non-leaf and leaf. Non-leaf
    stack_groups contain sub-stack_groups, while leaf
    stack_groups contain stacks. If a command is executed by a leaf
    stack_group, it should execute that command on the stacks it
    contains. If a command is executed by a non-leaf stack_group, it
    should invoke that command on each of its sub-stack_groups. This is
    done using the ``sceptre.helpers.recurse_into_sub_stack_groups``
    decorator.

    :param path: The name of the stack_group.
    :type path: str
    :param options: A dict of key-value pairs to update self.config with.
    :type debug: dict
    """

    def __init__(self, path, options=None):
        self.logger = logging.getLogger(__name__)
        self.path = path

        self.stacks = []
        self.sub_stack_groups = []
        self._options = {} if options is None else options

    def __repr__(self):
        return (
            "sceptre.stack_group.StackGroup("
            "path=\'{path}\', options=\'{options}\'"
            ")".format(path=self.path, options={})
        )
