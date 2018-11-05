# -*- coding: utf-8 -*-

"""
sceptre.plan.executor
This module implements a SceptrePlanExecutor, which is responsible for
executing the command specified in a SceptrePlan.
"""

from sceptre.plan.actions import StackActions


class SceptrePlanExecutor(object):

    def __init__(self):
        pass

    def execute(self, plan, *args):
        if plan.stack_group.stacks:
            for stack in plan.stack_group.stacks:
                response = getattr(StackActions(stack), plan.command)(*args)
                plan.responses.append(response)
        elif plan.stack_group.sub_stack_groups:
            for sub_stack_group in plan.stack_group.sub_stack_groups:
                for stack in sub_stack_group.stacks:
                    response = getattr(
                            StackActions(stack), plan.command)(*args)
                    plan.responses.append(response)
