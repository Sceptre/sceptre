import itertools
from collections import defaultdict
from typing import Optional, List, Set
from unittest.mock import create_autospec, Mock

import pytest

from sceptre.cli.launch import Launcher
from sceptre.context import SceptreContext
from sceptre.exceptions import DependencyDoesNotExistError
from sceptre.plan.plan import SceptrePlan
from sceptre.stack import Stack, LaunchAction
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
        self.executions.append(
            (self.command, self.launch_order.copy(), args)
        )
        return {
            stack: self.statuses_to_return[stack]
            for stack in self
        }

    def _generate_launch_order(self, reverse=False) -> List[Set[Stack]]:
        launch_order = [self.command_stacks]
        if self.context.ignore_dependencies:
            return launch_order

        all_stacks = list(self.all_stacks)

        for start_index in range(0, len(all_stacks), 2):
            chunk = {
                stack for stack in all_stacks[start_index: start_index + 2]
                if stack not in self.command_stacks
            }

            launch_order.append(chunk)

        return launch_order


class TestLauncher:

    def setup_method(self, test_method):
        self.plans: List[FakePlan] = []

        self.context = SceptreContext(
            project_path="project",
            command_path="my-test-group",
        )

        self.all_stacks = [
            Mock(spec=Stack, launch_action=LaunchAction.deploy, dependencies=[]),
            Mock(spec=Stack, launch_action=LaunchAction.deploy, dependencies=[]),
            Mock(spec=Stack, launch_action=LaunchAction.deploy, dependencies=[]),
            Mock(spec=Stack, launch_action=LaunchAction.deploy, dependencies=[]),
            Mock(spec=Stack, launch_action=LaunchAction.deploy, dependencies=[]),
            Mock(spec=Stack, launch_action=LaunchAction.deploy, dependencies=[])
        ]
        for index, stack in enumerate(self.all_stacks):
            stack.name = f'stacks/stack-{index}.yaml'

        self.command_stacks = [
            self.all_stacks[2],
            self.all_stacks[4]
        ]

        self.statuses_to_return = defaultdict(lambda: StackStatus.COMPLETE)

        self.plan_factory = create_autospec(SceptrePlan)
        self.plan_factory.side_effect = self.fake_plan_factory



        self.launcher = Launcher(self.context, self.plan_factory)

    def fake_plan_factory(self, sceptre_context):
        fake_plan = FakePlan(
            sceptre_context,
            set(self.command_stacks),
            set(self.all_stacks),
            self.statuses_to_return
        )
        self.plans.append(fake_plan)
        return fake_plan

    def get_executed_stacks(self, plan_number: int):
        launch_order = self.plans[plan_number].executions[0][1]
        return list(itertools.chain.from_iterable(launch_order))

    def test_launch__launches_stacks_marked_deploy(self):
        assert all(s.launch_action == LaunchAction.deploy for s in self.all_stacks)
        self.launcher.launch(True)

        launched_stacks = set(self.get_executed_stacks(0))
        expected_stacks = set(self.all_stacks)
        assert expected_stacks == launched_stacks
        assert self.plans[0].executions[0][0] == "launch"
        assert len(self.plans[0].executions) == 1

    def test_launch__no_deletions__returns_0(self):
        assert all(s.launch_action == LaunchAction.deploy for s in self.all_stacks)
        result = self.launcher.launch(True)

        assert result == 0

    @pytest.mark.parametrize("launch_action", [
        LaunchAction.skip,
        LaunchAction.delete
    ])
    def test_launch__does_not_launch_stacks_that_should_be_excluded(self, launch_action):
        self.all_stacks[4].launch_action = launch_action
        self.all_stacks[5].launch_action = launch_action

        self.launcher.launch(True)

        launched_stacks = set(self.get_executed_stacks(0))
        expected_stacks = {s for i, s in enumerate(self.all_stacks) if i not in (4, 5)}
        assert expected_stacks == launched_stacks
        assert self.plans[0].executions[0][0] == "launch"

    def test_launch__deletes_stacks_marked_with_delete_launch_action(self):
        self.all_stacks[4].launch_action = LaunchAction.delete
        self.all_stacks[5].launch_action = LaunchAction.delete

        self.launcher.launch(True)

        deleted_stacks = set(self.get_executed_stacks(1))
        expected_stacks = {self.all_stacks[4], self.all_stacks[5]}
        assert expected_stacks == deleted_stacks
        assert self.plans[1].executions[0][0] == "delete"
        assert self.plans[1].command_stacks == {self.all_stacks[4], self.all_stacks[5]}

    def test_launch__deletes_stacks_using_properly_configured_context_object(self):
        self.all_stacks[4].launch_action = LaunchAction.delete
        self.all_stacks[5].launch_action = LaunchAction.delete

        self.launcher.launch(True)

        delete_plan_context = next(p.context for p in self.plans if p.command == "delete")
        assert delete_plan_context.project_path == self.context.project_path
        assert delete_plan_context.command_path == self.context.command_path
        assert delete_plan_context.ignore_dependencies is True
        assert delete_plan_context.full_scan is True

    def test_launch__stack_with_dependency_marked_delete__raises_dependency_does_not_exist_error(self):
        self.all_stacks[0].launch_action = LaunchAction.delete
        self.all_stacks[1].dependencies.append(self.all_stacks[0])

        with pytest.raises(DependencyDoesNotExistError):
            self.launcher.launch(True)

    def test_launch__stacks_marked_delete__delete_and_deploy_actions_succeed__returns_0(self):
        self.all_stacks[0].launch_action = LaunchAction.delete

        code = self.launcher.launch(True)
        assert code == 0

    def test_launch__stacks_marked_delete__delete_action_fails__returns_nonzero(self):
        self.all_stacks[3].launch_action = LaunchAction.delete
        self.statuses_to_return[self.all_stacks[3]] = StackStatus.FAILED

        code = self.launcher.launch(True)
        assert code != 0

    def test_launch__deploy_action_fails__returns_nonzero(self):
        self.statuses_to_return[self.all_stacks[3]] = StackStatus.FAILED
        code = self.launcher.launch(True)
        assert code != 0
