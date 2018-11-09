# -*- coding: utf-8 -*-

import pytest
from mock import patch, sentinel, Mock, MagicMock

from botocore.exceptions import ClientError

from sceptre.exceptions import StackDoesNotExistError

from sceptre.stack_group import StackGroup
from sceptre.config.graph import StackDependencyGraph
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
        self.stack_group.project_path = "project_path"
        self.stack_group._options = {}
        response = self.stack_group.__repr__()
        assert response == \
            ("sceptre.stack_group.StackGroup(""path='path', options='{}')")

    @patch("sceptre.stack_group.StackGroup._build")
    @patch("sceptre.stack_group.StackGroup._get_launch_dependencies")
    @patch("sceptre.stack_group.StackGroup._get_initial_statuses")
    @patch("sceptre.stack_group.StackGroup._get_threading_events")
    def test_launch_calls_build_with_correct_args(
            self, mock_get_threading_events, mock_get_initial_statuses,
            mock_get_launch_dependencies, mock_build
    ):
        mock_get_threading_events.return_value = sentinel.threading_events
        mock_get_initial_statuses.return_value = sentinel.stack_statuses
        mock_get_launch_dependencies.return_value = \
            sentinel.dependencies

        self.stack_group.launch()

        mock_build.assert_called_once_with(
            "launch", sentinel.threading_events,
            sentinel.stack_statuses, sentinel.dependencies
        )

    def test_launch_succeeds_with_empty_group(self):
        self.stack_group.stacks = {}
        response = self.stack_group.launch()
        assert response == {}

    @patch("sceptre.stack_group.StackGroup._build")
    @patch("sceptre.stack_group.StackGroup._get_delete_dependencies")
    @patch("sceptre.stack_group.StackGroup._get_initial_statuses")
    @patch("sceptre.stack_group.StackGroup._get_threading_events")
    def test_delete_calls_build_with_correct_args(
            self, mock_get_threading_events, mock_get_initial_statuses,
            mock_get_delete_dependencies, mock_build
    ):
        mock_get_threading_events.return_value = sentinel.threading_events
        mock_get_initial_statuses.return_value = sentinel.stack_statuses
        mock_get_delete_dependencies.return_value = sentinel.dependencies

        self.stack_group.delete()

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
        dependencies = StackDependencyGraph({
            "stack_1": [], "stack_2": ["stack_1"]}
            )

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
        dependencies = StackDependencyGraph({"stack": []})

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
        dependencies = StackDependencyGraph({"stack": []})

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
            "prod/sg",
        ]

        expected_response = {
            "dev/mock_stack": ["dev/vpc", "dev/subnets", "prod/sg"],
            "dev/vpc": [],
            "dev/subnets": [],
            "prod/sg": []
        }

        self.stack_group.stacks = [mock_stack]
        response = self.stack_group._get_launch_dependencies()

        def dict_equality(response, expected):
            return set(response.as_dict()) == set(expected) and len(
                response.as_dict()) == len(expected)

        assert dict_equality(response, expected_response)

    def test_get_empty_launch_dependencies(self):
        mock_stack = MagicMock(spec=Stack)
        mock_stack.name = "dev/mock_stack"
        mock_stack.dependencies = []

        self.stack_group.stacks = [mock_stack]

        response = self.stack_group._get_launch_dependencies()

        assert response.as_dict() == {
            "dev/mock_stack": []
        }

    @patch("sceptre.stack_group.StackGroup._get_launch_dependencies")
    def test_get_delete_dependencies(self, mock_get_launch_dependencies):
        mock_get_launch_dependencies.return_value = StackDependencyGraph({
            "dev/mock_stack_1": [],
            "dev/mock_stack_2": [],
            "dev/mock_stack_3": ["dev/mock_stack_1", "dev/mock_stack_2"],
        })

        dependencies = self.stack_group._get_delete_dependencies()
        assert dependencies.as_dict() == {
            "dev/mock_stack_1": ["dev/mock_stack_3"],
            "dev/mock_stack_2": ["dev/mock_stack_3"],
            "dev/mock_stack_3": [],
        }
