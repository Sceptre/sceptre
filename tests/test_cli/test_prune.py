import functools
import itertools
from collections import defaultdict
from typing import Set, Optional, List
from unittest.mock import Mock, create_autospec

import pytest

from sceptre.cli.prune import Pruner, PATH_FOR_WHOLE_PROJECT
from sceptre.context import SceptreContext
from sceptre.exceptions import CannotPruneStackError
from sceptre.plan.plan import SceptrePlan
from sceptre.stack import Stack
from sceptre.stack_status import StackStatus


class FakePlan(SceptrePlan):
    def __init__(
        self,
        context: SceptreContext,
        command_stacks: Set[Stack],
        all_stacks: Set[Stack],
        statuses_to_return: dict,
    ):
        self.context = context
        self.command = None
        self.reverse = None
        self.launch_order: Optional[List[Set[Stack]]] = None

        self.all_stacks = self.graph = all_stacks
        self.command_stacks = command_stacks
        self.statuses_to_return = statuses_to_return

        self.executions = []

    def _execute(self, *args):
        self.executions.append((self.command, self.launch_order.copy(), args))
        return {stack: self.statuses_to_return[stack] for stack in self}

    def _generate_launch_order(self, reverse=False) -> List[Set[Stack]]:
        launch_order = [self.command_stacks]
        if self.context.ignore_dependencies:
            return launch_order

        all_stacks = list(self.all_stacks)

        for start_index in range(0, len(all_stacks), 2):
            chunk = {
                stack
                for stack in all_stacks[start_index : start_index + 2]
                if stack not in self.command_stacks
                and self._has_dependency_on_a_command_stack(stack)
            }
            if len(chunk):
                launch_order.append(chunk)

        return launch_order

    @functools.lru_cache()
    def _has_dependency_on_a_command_stack(self, stack):
        if len(self.command_stacks.intersection(stack.dependencies)):
            return True

        for dependency in stack.dependencies:
            if self._has_dependency_on_a_command_stack(dependency):
                return True

        return False


class TestPruner:
    def setup_method(self, test_method):
        self.plans: List[FakePlan] = []

        self.context = SceptreContext(
            project_path="project",
            command_path=PATH_FOR_WHOLE_PROJECT,
        )

        self.all_stacks = [
            Mock(spec=Stack, ignore=False, obsolete=False, dependencies=[]),
            Mock(spec=Stack, ignore=False, obsolete=False, dependencies=[]),
            Mock(spec=Stack, ignore=False, obsolete=False, dependencies=[]),
            Mock(spec=Stack, ignore=False, obsolete=False, dependencies=[]),
            Mock(spec=Stack, ignore=False, obsolete=False, dependencies=[]),
            Mock(spec=Stack, ignore=False, obsolete=False, dependencies=[]),
        ]
        for index, stack in enumerate(self.all_stacks):
            stack.name = f"stacks/stack-{index}.yaml"

        self.command_stacks = [self.all_stacks[2], self.all_stacks[4]]

        self.statuses_to_return = defaultdict(lambda: StackStatus.COMPLETE)

        self.plan_factory = create_autospec(SceptrePlan)
        self.plan_factory.side_effect = self.fake_plan_factory

        self.pruner = Pruner(self.context, self.plan_factory)

    def fake_plan_factory(self, sceptre_context):
        fake_plan = FakePlan(
            sceptre_context,
            set(self.command_stacks),
            set(self.all_stacks),
            self.statuses_to_return,
        )
        self.plans.append(fake_plan)
        return fake_plan

    @property
    def executed_stacks(self):
        assert len(self.plans) == 1
        launch_order = self.plans[0].executions[0][1]
        return list(itertools.chain.from_iterable(launch_order))

    def test_prune__no_obsolete_stacks__returns_zero(self):
        code = self.pruner.prune()
        assert code == 0

    def test_prune__no_obsolete_stacks__does_not_call_command_on_plan(self):
        self.pruner.prune()
        assert len(self.plans[0].executions) == 0

    def test_prune__whole_project__obsolete_stacks__deletes_all_obsolete_stacks(self):
        self.all_stacks[4].obsolete = True
        self.all_stacks[5].obsolete = True

        self.pruner.prune()

        assert self.plans[0].executions[0][0] == "delete"
        assert set(self.executed_stacks) == {self.all_stacks[4], self.all_stacks[5]}

    def test_prune__command_path__obsolete_stacks__deletes_only_obsolete_stacks_on_path(
        self,
    ):
        self.all_stacks[4].obsolete = True  # On command path
        self.all_stacks[5].obsolete = True  # not on command path
        self.context.command_path = "my/command/path"
        self.pruner.prune()

        assert self.plans[0].executions[0][0] == "delete"
        assert set(self.executed_stacks) == {self.all_stacks[4]}

    def test_prune__obsolete_stacks__returns_zero(self):
        self.all_stacks[4].obsolete = True
        self.all_stacks[5].obsolete = True

        code = self.pruner.prune()
        assert code == 0

    def test_prune__obsolete_stacks_depend_on_other_obsolete_stacks__deletes_only_obsolete_stacks(
        self,
    ):
        self.all_stacks[1].obsolete = True
        self.all_stacks[3].obsolete = True
        self.all_stacks[4].obsolete = True
        self.all_stacks[5].obsolete = True
        self.all_stacks[3].dependencies.append(self.all_stacks[1])
        self.all_stacks[4].dependencies.append(self.all_stacks[3])
        self.all_stacks[5].dependencies.append(self.all_stacks[3])

        self.pruner.prune()

        assert self.plans[0].executions[0][0] == "delete"
        assert set(self.executed_stacks) == {
            self.all_stacks[1],
            self.all_stacks[3],
            self.all_stacks[4],
            self.all_stacks[5],
        }

    def test_prune__non_obsolete_stacks_depend_on_obsolete_stacks__raises_cannot_prune_stack_error(
        self,
    ):
        self.all_stacks[1].obsolete = True
        self.all_stacks[3].obsolete = False
        self.all_stacks[4].obsolete = False
        self.all_stacks[5].obsolete = False
        self.all_stacks[3].dependencies.append(self.all_stacks[1])
        self.all_stacks[4].dependencies.append(self.all_stacks[3])
        self.all_stacks[5].dependencies.append(self.all_stacks[3])

        with pytest.raises(CannotPruneStackError):
            self.pruner.prune()

    def test_prune__non_obsolete_stacks_depend_on_obsolete_stacks__ignore_dependencies__deletes_obsolete_stacks(
        self,
    ):
        self.all_stacks[1].obsolete = True
        self.all_stacks[3].obsolete = False
        self.all_stacks[4].obsolete = False
        self.all_stacks[5].obsolete = False
        self.all_stacks[3].dependencies.append(self.all_stacks[1])
        self.all_stacks[4].dependencies.append(self.all_stacks[3])
        self.all_stacks[5].dependencies.append(self.all_stacks[3])
        self.context.ignore_dependencies = True
        self.pruner.prune()

        assert self.plans[0].executions[0][0] == "delete"
        assert set(self.executed_stacks) == {
            self.all_stacks[1],
        }

    def test_prune__delete_action_fails__returns_nonzero(self):
        self.all_stacks[1].obsolete = True
        self.statuses_to_return[self.all_stacks[1]] = StackStatus.FAILED

        code = self.pruner.prune()
        assert code != 0
