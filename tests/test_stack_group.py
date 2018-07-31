# -*- coding: utf-8 -*-

import pytest
from mock import patch, sentinel, Mock, MagicMock

from botocore.exceptions import ClientError

from sceptre.exceptions import CircularDependenciesError
from sceptre.exceptions import StackDoesNotExistError

from sceptre.stack_group import StackGroup
from sceptre.stack import Stack
from sceptre.stack_status import StackStatus


class TestStackGroup(object):

    def setup_method(self, test_method):
        self.stack_group = StackGroup(
            path="path",
            options=sentinel.options
        )

        # Run the rest of the tests against a leaf stack_group
        self.stack_group._is_leaf = True

    def test_initialise_stack_group(self):
        assert self.stack_group.path == "path"
        assert self.stack_group._options == sentinel.options
        assert self.stack_group.stacks == []
        assert self.stack_group.sub_stack_groups == []

    def test_initialise_stack_group_with_no_options(self):
        stack_group = StackGroup(path="path")
        assert stack_group.path == "path"
        assert stack_group._options == {}
        assert stack_group.stacks == []
        assert stack_group.sub_stack_groups == []

    def test_repr(self):
        self.stack_group.path = "path"
        self.stack_group.sceptre_dir = "sceptre_dir"
        self.stack_group._options = {}
        response = self.stack_group.__repr__()
        assert response == \
            ("sceptre.stack_group.StackGroup(""path='path', options='{}')")

    @patch("sceptre.stack_group.StackGroup._build")
    @patch("sceptre.stack_group.StackGroup._check_for_circular_dependencies")
    @patch("sceptre.stack_group.StackGroup._get_launch_dependencies")
    @patch("sceptre.stack_group.StackGroup._get_initial_statuses")
    @patch("sceptre.stack_group.StackGroup._get_threading_events")
    def test_launch_calls_build_with_correct_args(
            self, mock_get_threading_events, mock_get_initial_statuses,
            mock_get_launch_dependencies, mock_check_for_circular_dependencies,
            mock_build
    ):
        mock_get_threading_events.return_value = sentinel.threading_events
        mock_get_initial_statuses.return_value = sentinel.stack_statuses
        mock_get_launch_dependencies.return_value = \
            sentinel.dependencies

        self.stack_group.launch()

        mock_check_for_circular_dependencies.assert_called_once_with()
        mock_build.assert_called_once_with(
            "launch", sentinel.threading_events,
            sentinel.stack_statuses, sentinel.dependencies
        )

    def test_launch_succeeds_with_empty_group(self):
        self.stack_group.stacks = {}
        response = self.stack_group.launch()
        assert response == {}

    @patch("sceptre.stack_group.StackGroup._build")
    @patch("sceptre.stack_group.StackGroup._check_for_circular_dependencies")
    @patch("sceptre.stack_group.StackGroup._get_delete_dependencies")
    @patch("sceptre.stack_group.StackGroup._get_initial_statuses")
    @patch("sceptre.stack_group.StackGroup._get_threading_events")
    def test_delete_calls_build_with_correct_args(
            self, mock_get_threading_events, mock_get_initial_statuses,
            mock_get_delete_dependencies, mock_check_for_circular_dependencies,
            mock_build
    ):
        mock_get_threading_events.return_value = sentinel.threading_events
        mock_get_initial_statuses.return_value = sentinel.stack_statuses
        mock_get_delete_dependencies.return_value = sentinel.dependencies

        self.stack_group.delete()

        mock_check_for_circular_dependencies.assert_called_once_with()
        mock_build.assert_called_once_with(
            "delete", sentinel.threading_events,
            sentinel.stack_statuses, sentinel.dependencies
        )

    def test_delete_succeeds_with_empty_group(self):
        self.stack_group.stacks = {}
        response = self.stack_group.delete()
        assert response == {}

    def test_describe_with_running_stack(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"
        mock_stack.get_status.return_value = "status"
        self.stack_group.stacks = [mock_stack]

        response = self.stack_group.describe()
        assert response == {"stack": "status"}

    def test_describe_with_missing_stack(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"
        mock_stack.get_status.side_effect = StackDoesNotExistError()
        self.stack_group.stacks = [mock_stack]

        response = self.stack_group.describe()
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

        self.stack_group.stacks = [mock_stack]
        response = self.stack_group.describe_resources()
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

        self.stack_group.stacks = [mock_stack]
        response = self.stack_group.describe_resources()
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

        self.stack_group.stacks = [mock_stack]
        with pytest.raises(ClientError):
            self.stack_group.describe_resources()

    @patch("sceptre.stack_group.wait")
    @patch("sceptre.stack_group.ThreadPoolExecutor")
    def test_build(self, mock_ThreadPoolExecutor, mock_wait):
        self.stack_group.stacks = {"mock_stack": sentinel.stack}
        mock_ThreadPoolExecutor.return_value.__enter__.return_value\
            .submit.return_value = sentinel.future

        self.stack_group._build(
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

        self.stack_group._manage_stack_build(
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

        self.stack_group._manage_stack_build(
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

        self.stack_group._manage_stack_build(
            mock_stack,
            "launch",
            threading_events,
            stack_statuses,
            dependencies
        )

        assert stack_statuses["stack"] == StackStatus.FAILED
        # Check that that stack's event is set
        threading_events["stack"].set.assert_called_once_with()

    @patch("sceptre.stack_group.threading.Event")
    def test_get_threading_events(self, mock_Event):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"

        self.stack_group.stacks = [mock_stack]

        mock_Event.return_value = sentinel.event

        response = self.stack_group._get_threading_events()
        assert response == {
            "stack": sentinel.event
        }

    def test_get_initial_statuses(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"

        self.stack_group.stacks = [mock_stack]

        response = self.stack_group._get_initial_statuses()
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

        self.stack_group.stacks = [mock_stack]

        response = self.stack_group._get_launch_dependencies("dev")

        # Note that "prod/sg" is filtered out, because it's not under the
        # top level stack_group path "dev".
        assert response == {
            "dev/mock_stack": ["dev/vpc", "dev/subnets"]
        }

    @patch("sceptre.stack_group.StackGroup._get_launch_dependencies")
    def test_get_delete_dependencies(self, mock_get_launch_dependencies):
        mock_get_launch_dependencies.return_value = {
            "dev/mock_stack_1": [],
            "dev/mock_stack_2": [],
            "dev/mock_stack_3": ["dev/mock_stack_1", "dev/mock_stack_2"],
        }

        dependencies = self.stack_group._get_delete_dependencies()
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
        self.stack_group.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.stack_group._check_for_circular_dependencies()
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
        self.stack_group.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.stack_group._check_for_circular_dependencies()
        assert all(x in str(ex) for x in ['stack3', 'stack2', 'stack1'])

    def test_no_circular_dependencies_throws_no_error(self):
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack2"]
        stack1.name = "stack1"
        stack2.dependencies = []
        stack2.name = "stack2"
        stacks = [stack1, stack2]

        self.stack_group.stacks = stacks
        # Check this runs without throwing an exception
        self.stack_group._check_for_circular_dependencies()

    def test_no_circular_dependencies_with_nested_stacks(self):
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack1.dependencies = ["group1/stack2"]
        stack1.name = "stack1"
        stack2.dependencies = []
        stack2.name = "group1/stack2"
        stacks = [stack1, stack2]

        self.stack_group.stacks = stacks
        # Check this runs without throwing an exception
        self.stack_group._check_for_circular_dependencies()

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

        self.stack_group.stacks = stacks
        self.stack_group._check_for_circular_dependencies()

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

        self.stack_group.stacks = stacks
        self.stack_group._check_for_circular_dependencies()

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

        self.stack_group.stacks = stacks
        self.stack_group._check_for_circular_dependencies()

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

        self.stack_group.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.stack_group._check_for_circular_dependencies()
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

        self.stack_group.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.stack_group._check_for_circular_dependencies()
        assert (all(x in str(ex) for x in ['stack4', 'stack3', 'stack2']) and
                'stack1' not in str(ex))
