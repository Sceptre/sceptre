# -*- coding: utf-8 -*-

"""
sceptre.plan.executor
This module implements a SceptrePlanExecutor, which is responsible for
executing the command specified in a SceptrePlan.
"""

from sceptre.config.graph import StackDependencyGraph
from sceptre.plan.executor import SceptrePlanExecutor
from sceptre.plan.type import PlanType
from sceptre import stack, stack_group


class SceptrePlan(SceptrePlanExecutor):
    path = ""
    dependencies = StackDependencyGraph()
    launch_order = []
    command = ""
    plan_type = ""

    def __init__(self, path, command, subject):
        self.path = path
        self.command = command
        self.subject = subject
        if isinstance(self.subject, stack.Stack):
            self.plan_type = PlanType.STACK
        elif isinstance(self.subject,
                        stack_group.StackGroup):
            self.plan_type = PlanType.STACK_GROUP

    def execute(self, *args):
        return super(SceptrePlan, self).execute(self, *args)
