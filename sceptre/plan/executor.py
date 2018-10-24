# -*- coding: utf-8 -*-

"""
sceptre.plan.executor
This module implements a SceptrePlanExecutor, which is responsible for
executing the command specified in a SceptrePlan.
"""


class SceptrePlanExecutor(object):

    def __init__(self):
        pass

    def execute(self, plan, *args):
            return getattr(plan.subject, plan.command)(*args)
