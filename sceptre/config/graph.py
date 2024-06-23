# -*- coding: utf-8 -*-

"""
sceptre.config.graph

This module implements a StackGraph, which is represented as a directed
acyclic graph of a Stack's dependencies.
"""

import logging
from typing import List

import networkx as nx
from sceptre.exceptions import CircularDependenciesError
from sceptre.stack import Stack


class StackGraph(object):
    """
    A Directed Acyclic Graph representing the relationship between a Stack
    and its dependencies. Responsible for initalising the graph based on a set
    of Stacks.
    """

    def __init__(self, stacks):
        """
        Initialises a StackGraph based on a `set` of Stacks.

        :param stacks: A set of Stacks.
        :type stacks: set
        """
        self.logger = logging.getLogger(__name__)
        self.graph = nx.DiGraph()
        self._generate_graph(stacks)

    def __repr__(self):
        return str(nx.convert.to_dict_of_lists(self.graph))

    def __iter__(self):
        return self.graph.__iter__()

    def filtered(self, source_stacks, reverse=False):
        graph = (nx.reverse if reverse else nx.DiGraph)(self.graph)

        relevant = set(source_stacks)
        for stack in source_stacks:
            relevant |= nx.algorithms.dag.ancestors(graph, stack)
        graph.remove_nodes_from({stack for stack in graph if stack not in relevant})

        filtered = StackGraph(set())
        filtered.graph = graph

        return filtered

    def count_dependencies(self, stack):
        """
        Returns the number of incoming edges a given Stack has in the
        StackGraph. The number of incoming edge also represents the number
        of Stacks that depend on the given Stack.
        """
        return self.graph.in_degree(stack)

    def remove_stack(self, stack):
        """
        Removes a Stack from the StackGraph. This operation will also remove
        all adjecent edges that represent a 'depends on' relationship with
        other Stacks.
        """
        return self.graph.remove_node(stack)

    def _generate_graph(self, stacks):
        """
        Generates the graph for the StackGraph object.

        :param stacks: A set of Stacks
        :type stacks: set
        """

        for stack in stacks:
            self._generate_edges(stack, stack.dependencies)
        self.graph.remove_edges_from(nx.selfloop_edges(self.graph))

    def _generate_edges(self, stack: Stack, dependencies: List[Stack]):
        """
        Adds edges to the graph based on a list of dependencies that are
        generated from the initial stack config. Each of the paths
        in the inital_dependency_paths list are a depency that the inital
        Stack config depends on.

        :param stack: A Sceptre Stack
        :param dependencies: a collection of dependency paths
        """
        self.logger.debug(f"Generate dependencies for stack {stack}")
        for dependency in set(dependencies):
            self.graph.add_edge(dependency, stack)
            try:
                cycle = nx.find_cycle(self.graph, orientation="original")
                cycle_str = ", ".join([f"{edge[0]} -> {edge[1]}" for edge in cycle])
                raise CircularDependenciesError(
                    f"Dependency cycle detected: {cycle_str}"
                )
            except nx.NetworkXNoCycle:
                pass  # No cycle, continue
            self.logger.debug(f"  Added dependency: {dependency}")

        if not dependencies:
            self.graph.add_node(stack)
