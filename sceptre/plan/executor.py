# -*- coding: utf-8 -*-

"""
sceptre.plan.executor
This module implements a SceptrePlanExecutor, which is responsible for
executing the command specified in a SceptrePlan.
"""

from sceptre.plan.actions import StackActions
from botocore.exceptions import ClientError


class SceptrePlanExecutor(object):

    def __init__(self):
        pass

    def execute(self, plan, *args):
        if plan.stack_group.stacks:
            for stack in plan.stack_group.stacks:
                try:
                    response = getattr(
                        StackActions(stack), plan.command
                    )(*args)
                except(ClientError) as exp:
                    not_exists = exp.response.get("Error", {}).get("Message")
                    if not_exists and not_exists.endswith("does not exist"):
                        plan.errors.append(exp)
                        continue
                    else:
                        raise
                plan.responses.append(response)
        elif plan.stack_group.sub_stack_groups:
            for sub_stack_group in plan.stack_group.sub_stack_groups:
                for stack in sub_stack_group.stacks:
                    try:
                        response = getattr(
                                StackActions(stack), plan.command)(*args)
                    except(ClientError) as exp:
                        not_exists = exp.response.get(
                            "Error", {}
                        ).get("Message")
                        if not_exists and not_exists.endswith(
                            "does not exist"
                        ):
                            plan.errors.append(exp)
                            continue
                        else:
                            raise
                        plan.responses.append(response)
