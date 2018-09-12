# -*- coding: utf-8 -*-

"""
sceptre.config.graph
This module implements a StackConfig graph, which stores a directed graph
of a stack's dependencies.
"""

import logging
import networkx as nx
from sceptre.exceptions import CircularDependenciesError


class StackDependencyGraph(object):
    """
    A Directed Graph representing the relationship between Stack config
    dependencies. Responsible for initalizing the graph object based on
    a given inital stack config path.

    :param inital_config_path: The inital stack config you want to generate
    the graph from
    :type inital_config_path: str
    """

    def __init__(self, dependency_map=None):
        self.logger = logging.getLogger(__name__)
        self.graph = nx.DiGraph()
        if dependency_map is None:
            dependency_map = {}
        self.dependency_map = dependency_map
        self._generate_graph()

    def __repr__(self):
        return str(nx.convert.to_dict_of_lists(self.graph))

    def _generate_graph(self):
        """
        Generates the graph for the initalized StackDependencyGraph object
        """
        for stack, dependencies in self.dependency_map.items():
            self._generate_edges(stack, dependencies)

    def _is_acyclic(self):
        return nx.is_directed_acyclic_graph(self.graph)

    def _generate_edges(self, stack_path, dependency_paths):
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
        for dependency_path in dependency_paths:
            edge = self.graph.add_edge(stack_path, dependency_path)
            if not self._is_acyclic():
                raise CircularDependenciesError(
                    "Dependency cycle detected: {} {}".format(stack_path,
                                                              dependency_path))
            self.logger.debug("Added edge: {}".format(edge))

        if not dependency_paths:
            self.graph.add_node(stack_path)

        self.graph.remove_edges_from(nx.selfloop_edges(self.graph))

    def reverse_graph(self):
        rev = StackDependencyGraph({})
        rev.graph = nx.reverse(self.graph)
        return rev

    def update(self, other):
        self.graph = nx.compose(self.graph, other.graph)

    def as_dict(self):
        d = nx.convert.to_dict_of_lists(self.graph)
        for key in d.copy():
            if ".yaml" in key:
                d.pop(key)
        return d
