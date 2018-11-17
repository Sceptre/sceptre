# -*- coding: utf-8 -*-

"""
sceptre.stack_status

This module implemets structs for simplified Stack status and simplified
ChangeSet status values.
"""


class StackStatus(object):
    """
    StackStatus stores simplified Stack statuses.
    """
    COMPLETE = "complete"
    FAILED = "failed"
    IN_PROGRESS = "in progress"
    PENDING = "pending"


class StackChangeSetStatus(object):
    """
    StackChangeSetStatus stores simplified ChangeSet statuses.
    """
    PENDING = "pending"
    READY = "ready"
    DEFUNCT = "defunct"
