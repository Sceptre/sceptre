# -*- coding: utf-8 -*-

"""
sceptre.plan.executor

This module implements a SceptrePlanExecutor, which is responsible for
executing the command specified in a SceptrePlan.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set, Optional

from sceptre.plan.actions import StackActions
from sceptre.stack import Stack


class SceptrePlanExecutor(object):
    def __init__(
        self,
        command: str,
        launch_order: List[Set[Stack]],
        max_concurrency: Optional[int],
    ):
        """
        Initialises a SceptrePlanExecutor, generates the launch order, threads
        and intial Stack Statuses.

        :param command: The command to execute on the Stack.

        :param launch_order: A list containing sets of Stacks that can be executed concurrently.

        :param max_concurrency: Maximum number of threads to use for concurrent execution.
                                If None, uses the natural concurrency limit based on the largest batch.
        """

        self.logger = logging.getLogger(__name__)
        self.command = command
        self.launch_order = launch_order
        # Select the number of threads based upon the max batch size,
        # or use 1 if all batches are empty
        natural_concurrency = len(max(launch_order, key=len)) or 1
        if max_concurrency is not None and max_concurrency > 0:
            self.num_threads = min(max_concurrency, natural_concurrency)
        else:
            self.num_threads = natural_concurrency

    def execute(self, *args):
        """
        Execute is responsible executing the sets of Stacks in launch_order
        concurrently, in the correct order.

        :param args: Any arguments that should be passed through to the
                StackAction being called.
        """
        responses = {}

        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            for batch in self.launch_order:
                futures = [
                    executor.submit(self._execute, stack, *args) for stack in batch
                ]

                for future in as_completed(futures):
                    stack, status = future.result()
                    responses[stack] = status

        return responses

    def _execute(self, stack, *args):
        actions = StackActions(stack)
        result = getattr(actions, self.command)(*args)
        return stack, result
