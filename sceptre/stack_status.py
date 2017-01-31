# -*- coding: utf-8 -*-

"""
sceptre.stack_status

This module implemets structs for simplified stack status and simplified change
set status values.
"""


class StackStatus(object):
    """
    StackStatus stores simplified stack statuses.
    """
    COMPLETE = "complete"
    FAILED = "failed"
    IN_PROGRESS = "in progress"
    PENDING = "pending"


class StackChangeSetStatus(object):
    """
    StackChangeSetStatus stores simplified change set statuses.
    """
    PENDING = "pending"
    READY = "ready"
    DEFUNCT = "defunct"
