# -*- coding: utf-8 -*-

"""
sceptre.config.graph
This module implements a StackConfig graph, which stores a directed graph
of a stack's dependencies.
"""

import logging
import networkx as nx
from sceptre.exceptions import CircularDependenciesError


class StackGraph(object):
    """
    A Directed Graph representing the relationship between Stack config
    dependencies. Responsible for initalizing the graph object based on
    a given inital stack config path.
    """

    def __init__(self, stacks):
        """
        Graph that is based on a given `dependency_map`.

        :param dependency_map: A dict containing a list of the dependencies for
        a given stack
        :type dict: dict
        """
        self.logger = logging.getLogger(__name__)
        self.graph = nx.DiGraph()
        self._generate_graph(stacks)

    def __repr__(self):
        return str(nx.convert.to_dict_of_lists(self.graph))

    def __iter__(self):
        return self.graph.__iter__()

    def count_dependencies(self, stack):
        return self.graph.in_degree(stack)

    def remove_stack(self, stack):
        return self.graph.remove_node(stack)

    def write(self):
        nx.drawing.nx_pydot.write_dot(
            self.graph,
            './out.dot'
        )

        print(list(reversed(
            nx.algorithms.dag.dag_longest_path(self.graph)
        )))

        print(nx.convert.to_dict_of_lists(self.graph))

    def _generate_graph(self, stacks):
        """
        Generates the graph for the initalized StackDependencyGraph object
        """
        for stack in stacks:
            self._generate_edges(stack, stack.dependencies)
        self.graph.remove_edges_from(nx.selfloop_edges(self.graph))

    def _generate_edges(self, stack, dependencies):
        """
        Adds edges to the graph based on a list of dependencies that are
        generated from the inital stack config. Each of the paths
        in the inital_dependency_paths list are a depency that the inital
        Stack config depends on.

        :param dependency_paths: a collection of dependency paths
        :type inital_dependency_paths: string
        """
        self.logger.debug(
            "Generate edges for graph {0}".format(self.graph)
        )
        for dependency in dependencies:
            edge = self.graph.add_edge(dependency, stack)
            if not nx.is_directed_acyclic_graph(self.graph):
                raise CircularDependenciesError(
                    "Dependency cycle detected: {} {}".format(stack,
                                                              dependency))
            self.logger.debug("Added edge: {}".format(edge))

        if not dependencies:
            self.graph.add_node(stack)

    def reverse_graph(self):
        rev = StackGraph(set())
        rev.graph = nx.reverse(self.graph)
        return rev
