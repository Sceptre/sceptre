# -*- coding: utf-8 -*-

"""
sceptre.plan.executor
This module implements a SceptrePlanExecutor, which is responsible for
executing the command specified in a SceptrePlan.
"""
import networkx as nx
from sceptre.plan.actions import StackActions
from botocore.exceptions import ClientError
from sceptre.config.graph import StackDependencyGraph


class SceptrePlanExecutor(object):

    def __init__(self):
        pass

    def execute(self, plan, *args):
        # This is a temporary hack to ensure correct dependency order
        plan.stack_group.stacks = stack_dependency_resolution(
            plan.stack_group.stacks
        )

        for stack in plan.stack_group.stacks:
            try:
                result = getattr(StackActions(stack), plan.command)(*args)
            except(ClientError) as exp:
                not_exists = exp.response.get("Error", {}).get("Message")
                if not_exists and not_exists.endswith("does not exist"):
                    plan.errors.append(exp)
                    continue
                else:
                    raise
            plan.responses.append(result)


def stack_dependency_resolution(stacks):
    all_dependencies = {
        stack.name: stack.dependencies
        for stack in stacks
    }

    stack_graph = StackDependencyGraph(all_dependencies).graph
    stack_order = list(nx.topological_sort(stack_graph))
    stack_order.sort()

    ordered_stacks = []
    for stack_name in stack_order:
        stack = next(
            (stack for stack in stacks if stack.name == stack_name),
            None
        )

        if stack:
            ordered_stacks.append(stack)

    return ordered_stacks
