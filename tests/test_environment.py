# -*- coding: utf-8 -*-

import pytest
from mock import patch, sentinel, Mock, MagicMock

from botocore.exceptions import ClientError

from sceptre.exceptions import CircularDependenciesError
from sceptre.exceptions import StackDoesNotExistError

from sceptre.environment import Environment
from sceptre.stack import Stack
from sceptre.stack_status import StackStatus


class TestEnvironment(object):

    def setup_method(self, test_method):
        self.environment = Environment(
            path="path",
            options=sentinel.options
        )

        # Run the rest of the tests against a leaf environment
        self.environment._is_leaf = True

    def test_initialise_environment(self):
        assert self.environment.path == "path"
        assert self.environment._options == sentinel.options
        assert self.environment.stacks == []
        assert self.environment.environments == []

    def test_initialise_environment_with_no_options(self):
        environment = Environment(path="path")
        assert environment.path == "path"
        assert environment._options == {}
        assert environment.stacks == []
        assert environment.environments == []

    def test_repr(self):
        self.environment.path = "path"
        self.environment.sceptre_dir = "sceptre_dir"
        self.environment._options = {}
        response = self.environment.__repr__()
        assert response == (
            "sceptre.environment.Environment(path='path', options='{}')"
        )

    @patch("sceptre.environment.Environment._build")
    @patch("sceptre.environment.Environment._check_for_circular_dependencies")
    @patch("sceptre.environment.Environment._get_launch_dependencies")
    @patch("sceptre.environment.Environment._get_initial_statuses")
    @patch("sceptre.environment.Environment._get_threading_events")
    def test_launch_calls_build_with_correct_args(
            self, mock_get_threading_events, mock_get_initial_statuses,
            mock_get_launch_dependencies, mock_check_for_circular_dependencies,
            mock_build
    ):
        mock_get_threading_events.return_value = sentinel.threading_events
        mock_get_initial_statuses.return_value = sentinel.stack_statuses
        mock_get_launch_dependencies.return_value = \
            sentinel.dependencies

        self.environment.launch()

        mock_check_for_circular_dependencies.assert_called_once_with(
            sentinel.dependencies
        )
        mock_build.assert_called_once_with(
            "launch", sentinel.threading_events,
            sentinel.stack_statuses, sentinel.dependencies
        )

    @patch("sceptre.environment.Environment._build")
    @patch("sceptre.environment.Environment._check_for_circular_dependencies")
    @patch("sceptre.environment.Environment._get_delete_dependencies")
    @patch("sceptre.environment.Environment._get_initial_statuses")
    @patch("sceptre.environment.Environment._get_threading_events")
    def test_delete_calls_build_with_correct_args(
            self, mock_get_threading_events, mock_get_initial_statuses,
            mock_get_delete_dependencies, mock_check_for_circular_dependencies,
            mock_build
    ):
        mock_get_threading_events.return_value = sentinel.threading_events
        mock_get_initial_statuses.return_value = sentinel.stack_statuses
        mock_get_delete_dependencies.return_value = \
            sentinel.dependencies

        self.environment.delete()

        mock_check_for_circular_dependencies.assert_called_once_with(
            sentinel.dependencies
        )
        mock_build.assert_called_once_with(
            "delete", sentinel.threading_events,
            sentinel.stack_statuses, sentinel.dependencies
        )

    def test_describe_with_running_stack(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"
        mock_stack.get_status.return_value = "status"
        self.environment.stacks = [mock_stack]

        response = self.environment.describe()
        assert response == {"stack": "status"}

    def test_describe_with_missing_stack(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"
        mock_stack.get_status.side_effect = StackDoesNotExistError()
        self.environment.stacks = [mock_stack]

        response = self.environment.describe()
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

        self.environment.stacks = [mock_stack]
        response = self.environment.describe_resources()
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

        self.environment.stacks = [mock_stack]
        response = self.environment.describe_resources()
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

        self.environment.stacks = [mock_stack]
        with pytest.raises(ClientError):
            self.environment.describe_resources()

    @patch("sceptre.environment.wait")
    @patch("sceptre.environment.ThreadPoolExecutor")
    def test_build(self, mock_ThreadPoolExecutor, mock_wait):
        self.environment.stacks = {"mock_stack": sentinel.stack}
        mock_ThreadPoolExecutor.return_value.__enter__.return_value\
            .submit.return_value = sentinel.future

        self.environment._build(
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

        self.environment._manage_stack_build(
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

        self.environment._manage_stack_build(
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

        self.environment._manage_stack_build(
            mock_stack,
            "launch",
            threading_events,
            stack_statuses,
            dependencies
        )

        assert stack_statuses["stack"] == StackStatus.FAILED
        # Check that that stack's event is set
        threading_events["stack"].set.assert_called_once_with()

    @patch("sceptre.environment.threading.Event")
    def test_get_threading_events(self, mock_Event):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"

        self.environment.stacks = [mock_stack]

        mock_Event.return_value = sentinel.event

        response = self.environment._get_threading_events()
        assert response == {
            "stack": sentinel.event
        }

    def test_get_initial_statuses(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "stack"

        self.environment.stacks = [mock_stack]

        response = self.environment._get_initial_statuses()
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

        self.environment.stacks = [mock_stack]

        response = self.environment._get_launch_dependencies("dev")

        # Note that "prod/sg" is filtered out, because it's not under the
        # top level environment path "dev".
        assert response == {
            "dev/mock_stack": ["dev/vpc", "dev/subnets"]
        }

    @patch("sceptre.environment.Environment._get_launch_dependencies")
    def test_get_delete_dependencies(self, mock_get_launch_dependencies):
        mock_get_launch_dependencies.return_value = {
            "dev/mock_stack_1": [],
            "dev/mock_stack_2": [],
            "dev/mock_stack_3": ["dev/mock_stack_1", "dev/mock_stack_2"],
        }

        dependencies = self.environment._get_delete_dependencies()
        assert dependencies == {
            "dev/mock_stack_1": ["dev/mock_stack_3"],
            "dev/mock_stack_2": ["dev/mock_stack_3"],
            "dev/mock_stack_3": [],
        }

    def test_check_for_circular_dependencies_with_circular_dependencies(self):
        dependencies = {
            "stack-1": ["stack-2"],
            "stack-2": ["stack-1"]
        }

        with pytest.raises(CircularDependenciesError):
            self.environment._check_for_circular_dependencies(dependencies)

    def test_check_for_circular_dependencies_without_find_dependencies(self):
        dependencies = {
            "stack-1": ["stack-2"],
            "stack-2": []
        }

        # Check this runs without throwing an exception
        self.environment._check_for_circular_dependencies(dependencies)
