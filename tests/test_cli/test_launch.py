import functools
import itertools
from collections import defaultdict
from typing import Optional, List, Set
from unittest.mock import create_autospec, Mock

import pytest

from sceptre.cli.launch import Launcher
from sceptre.cli.prune import Pruner
from sceptre.context import SceptreContext
from sceptre.exceptions import DependencyDoesNotExistError
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

        self.all_stacks = all_stacks
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


class TestLauncher:
    def setup_method(self, test_method):
        self.plans: List[FakePlan] = []

        self.context = SceptreContext(
            project_path="project",
            command_path="my-test-group",
        )
        self.cloned_context = self.context.clone()
        # Since contexts don't have a __eq__ method, you can't assert easily off the result of
        # clone without some hijinks.
        self.context = Mock(
            wraps=self.context,
            **{"clone.return_value": self.cloned_context, "ignore_dependencies": False},
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

        self.command_stacks = list(self.all_stacks)

        self.statuses_to_return = defaultdict(lambda: StackStatus.COMPLETE)

        self.fake_pruner = Mock(spec=Pruner, **{"prune.return_value": 0})

        self.plan_factory = create_autospec(SceptrePlan)
        self.plan_factory.side_effect = self.fake_plan_factory
        self.pruner_factory = create_autospec(Pruner)
        self.pruner_factory.return_value = self.fake_pruner

        self.launcher = Launcher(self.context, self.plan_factory, self.pruner_factory)

    def fake_plan_factory(self, sceptre_context):
        fake_plan = FakePlan(
            sceptre_context,
            set(self.command_stacks),
            set(self.all_stacks),
            self.statuses_to_return,
        )
        self.plans.append(fake_plan)
        return fake_plan

    def get_executed_stacks(self, plan_number: int):
        launch_order = self.plans[plan_number].executions[0][1]
        return list(itertools.chain.from_iterable(launch_order))

    def test_launch__launches_stacks_that_are_neither_ignored_nor_obsolete(self):
        assert all(not s.ignore and not s.obsolete for s in self.all_stacks)
        self.command_stacks = self.all_stacks
        self.launcher.launch(True)
        launched_stacks = set(self.get_executed_stacks(0))
        expected_stacks = set(self.all_stacks)
        assert expected_stacks == launched_stacks
        assert self.plans[0].executions[0][0] == "launch"
        assert len(self.plans[0].executions) == 1

    def test_launch__prune__no_obsolete_stacks__does_not_delete_any_stacks(self):
        assert all(not s.obsolete for s in self.all_stacks)
        self.launcher.launch(True)
        assert len(self.plans) == 1
        assert self.plans[0].executions[0][0] == "launch"

    def test_launch__prune__instantiates_and_invokes_pruner(self):
        self.launcher.launch(True)
        self.fake_pruner.prune.assert_any_call()

    def test_launch__no_prune__obsolete_stacks__does_not_delete_any_stacks(self):
        self.all_stacks[4].obsolete = True
        self.all_stacks[5].obsolete = True

        self.launcher.launch(False)
        assert len(self.plans) == 1
        assert self.plans[0].executions[0][0] == "launch"

    @pytest.mark.parametrize(
        "prune", [pytest.param(True, id="prune"), pytest.param(False, id="no prune")]
    )
    def test_launch__returns_0(self, prune):
        assert all(not s.ignore and not s.obsolete for s in self.all_stacks)
        result = self.launcher.launch(prune)

        assert result == 0

    def test_launch__does_not_launch_stacks_that_should_be_excluded(self):
        self.all_stacks[4].ignore = True
        self.all_stacks[5].obsolete = True

        self.launcher.launch(True)

        launched_stacks = set(self.get_executed_stacks(0))
        expected_stacks = {s for i, s in enumerate(self.all_stacks) if i not in (4, 5)}
        assert expected_stacks == launched_stacks
        assert self.plans[0].executions[0][0] == "launch"

    def test_launch__prune__stack_with_dependency_marked_obsolete__raises_dependency_does_not_exist_error(
        self,
    ):
        self.all_stacks[0].obsolete = True
        self.all_stacks[1].dependencies.append(self.all_stacks[0])

        self.command_stacks = [self.all_stacks[0]]

        with pytest.raises(DependencyDoesNotExistError):
            self.launcher.launch(True)

    def test_launch__prune__ignore_dependencies__stack_with_dependency_marked_obsolete__raises_no_error(
        self,
    ):
        self.all_stacks[0].obsolete = True
        self.all_stacks[1].dependencies.append(self.all_stacks[0])

        self.command_stacks = [self.all_stacks[0]]
        self.context.ignore_dependencies = True
        self.launcher.launch(True)

    def test_launch__no_prune__does_not_raise_error(self):
        self.all_stacks[0].obsolete = True
        self.all_stacks[1].dependencies.append(self.all_stacks[0])
        self.launcher.launch(False)

    def test_launch__stacks_are_pruned__delete_and_deploy_actions_succeed__returns_0(
        self,
    ):
        self.all_stacks[0].obsolete = True

        code = self.launcher.launch(True)
        assert code == 0

    def test_launch__pruner_returns_nonzero__returns_nonzero(self):
        self.fake_pruner.prune.return_value = 99

        code = self.launcher.launch(True)
        assert code == 99

    def test_launch__deploy_action_fails__returns_nonzero(self):
        self.statuses_to_return[self.all_stacks[3]] = StackStatus.FAILED
        code = self.launcher.launch(False)
        assert code != 0
