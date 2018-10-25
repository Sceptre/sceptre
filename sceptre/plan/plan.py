# -*- coding: utf-8 -*-

"""
sceptre.plan.executor
This module implements a SceptrePlanExecutor, which is responsible for
executing the command specified in a SceptrePlan.
"""

from sceptre.plan.actions import StackActions
from sceptre.plan.executor import SceptrePlanExecutor
from sceptre.plan.type import PlanType
from sceptre.stack import Stack
from sceptre.stack_group import StackGroup


class SceptrePlan(SceptrePlanExecutor):

    def __init__(self, context, command, subject):
        self.context = context
        self.command = command
        self.subject = subject
        self.actions = self._determine_actions(subject)

    def execute(self, *args):
        return super(SceptrePlan, self).execute(self, *args)

    def _determine_actions(self, subject):
        if isinstance(self.subject, Stack):
            self.plan_type = PlanType.STACK
            return StackActions(self.subject)
        elif isinstance(self.subject,
                        StackGroup):
            self.plan_type = PlanType.STACK_GROUP
