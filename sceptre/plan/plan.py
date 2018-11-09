# -*- coding: utf-8 -*-

"""
sceptre.plan.executor
This module implements a SceptrePlanExecutor, which is responsible for
executing the command specified in a SceptrePlan.
"""

from sceptre.plan.executor import SceptrePlanExecutor
from sceptre.plan.type import PlanType
from sceptre.stack import Stack
from sceptre.stack_group import StackGroup


class SceptrePlan(SceptrePlanExecutor):

    def __init__(self, context, command, subject):
        self.context = context
        self.command = command
        self.subject = subject
        if isinstance(self.subject, Stack):
            self.plan_type = PlanType.STACK
        elif isinstance(self.subject,
                        StackGroup):
            self.plan_type = PlanType.STACK_GROUP

    def execute(self, *args):
        return super(SceptrePlan, self).execute(self, *args)
