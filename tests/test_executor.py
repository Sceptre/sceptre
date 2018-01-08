# -*- coding: utf-8 -*-

import pytest
from mock import patch, sentinel, Mock, MagicMock

from botocore.exceptions import ClientError

from sceptre.exceptions import CircularDependenciesError
from sceptre.exceptions import StackDoesNotExistError

from sceptre.executor import Executor
from sceptre.stack import Stack
from sceptre.stack_status import StackStatus


class TestExecutor(object):

    def setup_method(self, test_method):
        self.executor = Executor(
            path="path",
            options=sentinel.options
        )

        # Run the rest of the tests against a leaf executor
        self.executor._is_leaf = True

    def test_initialise_executor(self):
        assert self.executor.path == "path"
        assert self.executor._options == sentinel.options
        assert self.executor.stacks == []
        assert self.executor.sub_executors == []

    def test_initialise_executor_with_no_options(self):
        executor = Executor(path="path")
        assert executor.path == "path"
        assert executor._options == {}
        assert executor.stacks == []
        assert executor.sub_executors == []

    def test_repr(self):
        self.executor.path = "path"
        self.executor.sceptre_dir = "sceptre_dir"
        self.executor._options = {}
        response = self.executor.__repr__()
        assert response == \
            ("sceptre.executor.Executor(""path='path', options='{}')")

    @patch("sceptre.executor.Executor._build")
    @patch("sceptre.executor.Executor._check_for_circular_dependencies")
    @patch("sceptre.executor.Executor._get_launch_dependencies")
    @patch("sceptre.executor.Executor._get_initial_statuses")
    @patch("sceptre.executor.Executor._get_threading_events")
    def test_launch_calls_build_with_correct_args(
            self, mock_get_threading_events, mock_get_initial_statuses,
            mock_get_launch_dependencies, mock_check_for_circular_dependencies,
            mock_build
    ):
        mock_get_threading_events.return_value = sentinel.threading_events
        mock_get_initial_statuses.return_value = sentinel.stack_statuses
        mock_get_launch_dependencies.return_value = \
            sentinel.dependencies

        self.executor.launch()

        mock_check_for_circular_dependencies.assert_called_once_with()
        mock_build.assert_called_once_with(
            "launch", sentinel.threading_events,
            sentinel.stack_statuses, sentinel.dependencies
        )

    def test_launch_succeeds_with_empty_env(self):
        self.executor.stacks = {}
        response = self.executor.launch()
        assert response == {}

    @patch("sceptre.executor.Executor._build")
    @patch("sceptre.executor.Executor._check_for_circular_dependencies")
    @patch("sceptre.executor.Executor._get_delete_dependencies")
    @patch("sceptre.executor.Executor._get_initial_statuses")
    @patch("sceptre.executor.Executor._get_threading_events")
    def test_delete_calls_build_with_correct_args(
            self, mock_get_threading_events, mock_get_initial_statuses,
            mock_get_delete_dependencies, mock_check_for_circular_dependencies,
            mock_build
    ):
        mock_get_threading_events.return_value = sentinel.threading_events
        mock_get_initial_statuses.return_value = sentinel.stack_statuses
        mock_get_delete_dependencies.return_value = sentinel.dependencies

        self.executor.delete()

        mock_check_for_circular_dependencies.assert_called_once_with()
        mock_build.assert_called_once_with(
            "delete", sentinel.threading_events,
            sentinel.stack_statuses, sentinel.dependencies
        )

    def test_delete_succeeds_with_empty_env(self):
        self.executor.stacks = {}
        response = self.executor.delete()
        assert response == {}

    def test_describe_with_running_stack(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"
        mock_stack.get_status.return_value = "status"
        self.executor.stacks = [mock_stack]

        response = self.executor.describe()
        assert response == {"stack": "status"}

    def test_describe_with_missing_stack(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"
        mock_stack.get_status.side_effect = StackDoesNotExistError()
        self.executor.stacks = [mock_stack]

        response = self.executor.describe()
        assert response == {"stack": "PENDING"}

    def test_describe_resources_forms_response(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"
        mock_stack.describe_resources.return_value = [
            {
                "LogicalResourceId": sentinel.logical_resource_id,
                "PhysicalResourceId": sentinel.physical_resource_id
            }
        ]

        self.executor.stacks = [mock_stack]
        response = self.executor.describe_resources()
        assert response == {
            "stack": [
                {
                    "LogicalResourceId": sentinel.logical_resource_id,
                    "PhysicalResourceId": sentinel.physical_resource_id
                }
            ]
        }

    def test_describe_resources_ignores_stack_does_not_exist_exception(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"
        mock_stack.describe_resources.side_effect = ClientError(
            {
                "Error": {
                    "Code": 500,
                    "Message": "stack does not exist"
                }
            },
            sentinel.operation
        )

        self.executor.stacks = [mock_stack]
        response = self.executor.describe_resources()
        assert response == {}

    def test_describe_resources_raises_other_client_errors(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"
        mock_stack.describe_resources.side_effect = ClientError(
            {
                "Error": {
                    "Code": 500,
                    "Message": "Boom!"
                }
            },
            sentinel.operation
        )

        self.executor.stacks = [mock_stack]
        with pytest.raises(ClientError):
            self.executor.describe_resources()

    @patch("sceptre.executor.wait")
    @patch("sceptre.executor.ThreadPoolExecutor")
    def test_build(self, mock_ThreadPoolExecutor, mock_wait):
        self.executor.stacks = {"mock_stack": sentinel.stack}
        mock_ThreadPoolExecutor.return_value.__enter__.return_value\
            .submit.return_value = sentinel.future

        self.executor._build(
            sentinel.command, sentinel.threading_events,
            sentinel.stack_statuses, sentinel.dependencies
        )

        mock_wait.assert_called_once_with([sentinel.future])

    def test_manage_stack_build_with_failed_dependency(self):
        threading_events = {"stack_1": Mock(), "stack_2": Mock()}
        stack_statuses = {
            "stack_1": StackStatus.FAILED,
            "stack_2": StackStatus.PENDING
        }
        dependencies = {"stack_1": [], "stack_2": ["stack_1"]}

        mock_stack_2 = Mock()
        mock_stack_2.name = "stack_2"

        self.executor._manage_stack_build(
            mock_stack_2,
            sentinel.command,
            threading_events,
            stack_statuses,
            dependencies
        )

        assert stack_statuses["stack_2"] == StackStatus.FAILED
        # Check that that stack's event is set
        threading_events["stack_2"].set.assert_called_once_with()

    def test_manage_stack_build_with_sucessful_command(self):
        threading_events = {"stack": Mock()}
        stack_statuses = {"stack": StackStatus.PENDING}
        dependencies = {"stack": []}

        mock_stack = Mock()
        mock_stack.name = "stack"
        mock_stack.launch.return_value = StackStatus.COMPLETE

        self.executor._manage_stack_build(
            mock_stack,
            "launch",
            threading_events,
            stack_statuses,
            dependencies
        )

        assert stack_statuses["stack"] == StackStatus.COMPLETE
        # Check that that stack's event is set
        threading_events["stack"].set.assert_called_once_with()

    def test_manage_stack_build_with_unsucessful_command(self):
        threading_events = {"stack": Mock()}
        stack_statuses = {"stack": StackStatus.PENDING}
        dependencies = {"stack": []}

        mock_stack = Mock()
        mock_stack.name = "stack"
        mock_stack.launch.side_effect = Exception()

        self.executor._manage_stack_build(
            mock_stack,
            "launch",
            threading_events,
            stack_statuses,
            dependencies
        )

        assert stack_statuses["stack"] == StackStatus.FAILED
        # Check that that stack's event is set
        threading_events["stack"].set.assert_called_once_with()

    @patch("sceptre.executor.threading.Event")
    def test_get_threading_events(self, mock_Event):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"

        self.executor.stacks = [mock_stack]

        mock_Event.return_value = sentinel.event

        response = self.executor._get_threading_events()
        assert response == {
            "stack": sentinel.event
        }

    def test_get_initial_statuses(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"

        self.executor.stacks = [mock_stack]

        response = self.executor._get_initial_statuses()
        assert response == {
            "stack": StackStatus.PENDING
        }

    def test_get_launch_dependencies(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "dev/mock_stack"

        mock_stack.dependencies = [
            "dev/vpc",
            "dev/subnets",
            "prod/sg"
        ]

        self.executor.stacks = [mock_stack]

        response = self.executor._get_launch_dependencies("dev")

        # Note that "prod/sg" is filtered out, because it's not under the
        # top level executor path "dev".
        assert response == {
            "dev/mock_stack": ["dev/vpc", "dev/subnets"]
        }

    @patch("sceptre.executor.Executor._get_launch_dependencies")
    def test_get_delete_dependencies(self, mock_get_launch_dependencies):
        mock_get_launch_dependencies.return_value = {
            "dev/mock_stack_1": [],
            "dev/mock_stack_2": [],
            "dev/mock_stack_3": ["dev/mock_stack_1", "dev/mock_stack_2"],
        }

        dependencies = self.executor._get_delete_dependencies()
        assert dependencies == {
            "dev/mock_stack_1": ["dev/mock_stack_3"],
            "dev/mock_stack_2": ["dev/mock_stack_3"],
            "dev/mock_stack_3": [],
        }

    def test_check_for_circular_dependencies_with_circular_dependencies(self):
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack2"]
        stack1.name = "stack1"
        stack2.dependencies = ["stack1"]
        stack2.name = "stack2"
        stacks = [stack1, stack2]
        self.executor.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.executor._check_for_circular_dependencies()
        assert all(x in str(ex) for x in ['stack2', 'stack1'])

    def test_circular_dependencies_with_3_circular_dependencies(self):
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack3 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack2"]
        stack1.name = "stack1"
        stack2.dependencies = ["stack3"]
        stack2.name = "stack2"
        stack3.dependencies = ["stack1"]
        stack3.name = "stack3"
        stacks = [stack1, stack2, stack3]
        self.executor.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.executor._check_for_circular_dependencies()
        assert all(x in str(ex) for x in ['stack3', 'stack2', 'stack1'])

    def test_no_circular_dependencies_throws_no_error(self):
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack2"]
        stack1.name = "stack1"
        stack2.dependencies = []
        stack2.name = "stack2"
        stacks = [stack1, stack2]

        self.executor.stacks = stacks
        # Check this runs without throwing an exception
        self.executor._check_for_circular_dependencies()

    def test_no_circular_dependencies_with_nested_stacks(self):
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack1.dependencies = ["env1/stack2"]
        stack1.name = "stack1"
        stack2.dependencies = []
        stack2.name = "env1/stack2"
        stacks = [stack1, stack2]

        self.executor.stacks = stacks
        # Check this runs without throwing an exception
        self.executor._check_for_circular_dependencies()

    def test_DAG_diamond_throws_no_circ_dependencies_error(self):
        """
        Ensures
            o
           / \
          o   o
           \ /
            o
        throws no circular dependency error
        """
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack3 = MagicMock(Spec=Stack)
        stack4 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack2", "stack3"]
        stack1.name = "stack1"
        stack2.dependencies = ["stack4"]
        stack2.name = "stack2"
        stack3.dependencies = ["stack4"]
        stack3.name = "stack3"
        stack4.dependencies = []
        stack4.name = "stack4"
        stacks = [stack1, stack2, stack3, stack4]

        self.executor.stacks = stacks
        self.executor._check_for_circular_dependencies()

    def test_modified_DAG_diamond_throws_no_circ_dependencies_error(self):
        """
        Ensures
            o
           / \
          o   o
           \ / \
            o   o
        throws no circular dependency error
        """
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack3 = MagicMock(Spec=Stack)
        stack4 = MagicMock(Spec=Stack)
        stack5 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack2", "stack3"]
        stack1.name = "stack1"
        stack2.dependencies = ["stack4"]
        stack2.name = "stack2"
        stack3.dependencies = ["stack4", "stack5"]
        stack3.name = "stack3"
        stack4.dependencies = []
        stack4.name = "stack4"
        stack5.dependencies = []
        stack5.name = "stack5"
        stacks = [stack1, stack2, stack3, stack4, stack5]

        self.executor.stacks = stacks
        self.executor._check_for_circular_dependencies()

    def test_DAG_diamond_with_triangle_throws_no_circ_dependencies_error(self):
        """
        Ensures
            o
           / \
          o   o
           \ / \
            o ->o
        throws no circular dependency error
        """
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack3 = MagicMock(Spec=Stack)
        stack4 = MagicMock(Spec=Stack)
        stack5 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack2", "stack3"]
        stack1.name = "stack1"
        stack2.dependencies = ["stack4"]
        stack2.name = "stack2"
        stack3.dependencies = ["stack4", "stack5"]
        stack3.name = "stack3"
        stack4.dependencies = ["stack5"]
        stack4.name = "stack4"
        stack5.dependencies = []
        stack5.name = "stack5"
        stacks = [stack1, stack2, stack3, stack4, stack5]

        self.executor.stacks = stacks
        self.executor._check_for_circular_dependencies()

    def test_4_cycle_throws_circ_dependencies_error(self):
        """
        Ensures
            o - o
            |   |
            o - o
        throws circular dependency error
        """
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack3 = MagicMock(Spec=Stack)
        stack4 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack4"]
        stack1.name = "stack1"
        stack2.dependencies = ["stack1"]
        stack2.name = "stack2"
        stack3.dependencies = ["stack2"]
        stack3.name = "stack3"
        stack4.dependencies = ["stack3"]
        stack4.name = "stack4"
        stacks = [stack1, stack2, stack3, stack4]

        self.executor.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.executor._check_for_circular_dependencies()
        assert all(x in str(ex) for x in ['stack4', 'stack3', 'stack2',
                                          'stack1'])

    def test_modified_3_cycle_throws_circ_dependencies_error(self):
        """
        Ensures
            o   o
             \ / \
              o - o
              (right triangle is a 3 cycle)
        throws circular dependency error
        """
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack3 = MagicMock(Spec=Stack)
        stack4 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack2"]
        stack1.name = "stack1"
        stack2.dependencies = ["stack3"]
        stack2.name = "stack2"
        stack3.dependencies = ["stack4"]
        stack3.name = "stack3"
        stack4.dependencies = ["stack2"]
        stack4.name = "stack4"
        stacks = [stack1, stack2, stack3, stack4]

        self.executor.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.executor._check_for_circular_dependencies()
        assert (all(x in str(ex) for x in ['stack4', 'stack3', 'stack2']) and
                'stack1' not in str(ex))
