# -*- coding: utf-8 -*-

import os
import pytest
from mock import patch, sentinel, MagicMock, Mock, PropertyMock

from botocore.exceptions import ClientError

from sceptre.exceptions import CircularDependenciesError
from sceptre.exceptions import StackDoesNotExistError
from sceptre.exceptions import InvalidEnvironmentPathError

from sceptre.environment import Environment
from sceptre.stack_status import StackStatus
from sceptre.stack import Stack


class TestEnvironment(object):

    @patch("sceptre.environment.Environment._load_stacks")
    @patch(
        "sceptre.environment.Environment.is_leaf", new_callable=PropertyMock
    )
    @patch("sceptre.environment.Environment._validate_path")
    def setup_method(
            self, test_method, mock_validate_path,
            mock_is_leaf, mock_load_stacks
    ):
        mock_is_leaf.return_value = True
        mock_load_stacks.return_value = sentinel.stacks
        mock_validate_path.return_value = "environment_path"

        self.environment = Environment(
            sceptre_dir="sceptre_dir",
            environment_path="environment_path",
            options=sentinel.options
        )

        # Run the rest of the tests against a leaf environment
        self.environment._is_leaf = True

    def test_initialise_environment(self):
        assert self.environment.sceptre_dir == "sceptre_dir"
        assert self.environment.path == "environment_path"
        assert self.environment._options == sentinel.options
        assert self.environment.is_leaf is True
        assert self.environment.stacks == sentinel.stacks

    @patch("sceptre.environment.Environment._load_environments")
    @patch(
        "sceptre.environment.Environment.is_leaf", new_callable=PropertyMock
    )
    @patch("sceptre.environment.Environment._validate_path")
    def test_initialise_environment_with_non_leaf_directory(
            self, mock_validate_path,
            mock_is_leaf, mock_load_environments
    ):
        mock_is_leaf.return_value = False
        mock_load_environments.return_value = sentinel.environments

        environment = Environment(
            sceptre_dir="sceptre_dir",
            environment_path="environment_path",
            options=sentinel.options
        )

        assert environment.environments == sentinel.environments

    def test_repr(self):
        self.environment.path = "path"
        self.environment.sceptre_dir = "sceptre_dir"
        self.environment._options = {}
        response = self.environment.__repr__()
        assert response == (
            "sceptre.environment.Environment(sceptre_dir='sceptre_dir', "
            "environment_path='path', options={})"
        )

    def test_validate_path_with_valid_path(self):
        path = self.environment._validate_path("valid/env/path")
        assert path == "valid/env/path"

    def test_validate_path_with_backslashes_in_path(self):
        path = self.environment._validate_path("valid\env\path")
        assert path == "valid/env/path"

    def test_validate_path_with_double_backslashes_in_path(self):
        path = self.environment._validate_path("valid\\env\\path")
        assert path == "valid/env/path"

    def test_validate_path_with_leading_slash(self):
        with pytest.raises(InvalidEnvironmentPathError):
            self.environment._validate_path(
                "/this/environment/path/is/invalid"
            )

    def test_validate_path_with_leading_backslash(self):
        with pytest.raises(InvalidEnvironmentPathError):
            self.environment._validate_path(
                "\\this\environment\path\is\invalid"
            )

    def test_validate_path_with_trailing_slash(self):
        with pytest.raises(InvalidEnvironmentPathError):
            self.environment._validate_path(
                "this/environment/path/is/invalid/"
            )

    def test_validate_path_with_trailing_backslash(self):
        with pytest.raises(InvalidEnvironmentPathError):
            self.environment._validate_path(
                "this\environment\path\is\invalid\\"
            )

    def test_is_leaf_with_leaf_dir(self):
        self.environment.sceptre_dir = os.path.join(
            os.getcwd(), "tests", "fixtures"
        )
        self.environment.path = os.path.join(
            "account", "environment", "region"
        )
        self.environment._is_leaf = None
        assert self.environment.is_leaf is True

    def test_is_leaf_with_non_leaf_dir(self):
        self.environment.sceptre_dir = os.path.join(
            os.getcwd(), "tests", "fixtures"
        )
        self.environment.path = os.path.join(
            "account", "environment"
        )
        self.environment._is_leaf = None
        assert self.environment.is_leaf is False

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

        mock_check_for_circular_dependencies.assert_called_once_with()
        mock_build.assert_called_once_with(
            "launch", sentinel.threading_events,
            sentinel.stack_statuses, sentinel.dependencies
        )

    def test_launch_succeeds_with_empty_env(self):
        self.environment.stacks = {}
        response = self.environment.launch()
        assert response == {}

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

        mock_check_for_circular_dependencies.assert_called_once_with()
        mock_build.assert_called_once_with(
            "delete", sentinel.threading_events,
            sentinel.stack_statuses, sentinel.dependencies
        )

    def test_delete_succeeds_with_empty_env(self):
        self.environment.stacks = {}
        response = self.environment.delete()
        assert response == {}

    def test_describe_with_running_stack(self):
        mock_stack = Mock()
        mock_stack.name = "stack"
        mock_stack.get_status.return_value = "status"
        self.environment.stacks = {"name": mock_stack}

        response = self.environment.describe()
        assert response == {"stack": "status"}

    def test_describe_with_missing_stack(self):
        mock_stack = Mock()
        mock_stack.name = "stack"
        mock_stack.get_status.side_effect = StackDoesNotExistError
        self.environment.stacks = {"stack": mock_stack}

        response = self.environment.describe()
        assert response == {"stack": "PENDING"}

    def test_describe_resources_forms_response(self):
        mock_stack = Mock()
        mock_stack.name = "stack-name"
        mock_stack.describe_resources.return_value = [
            {
                "LogicalResourceId": sentinel.logical_resource_id,
                "PhysicalResourceId": sentinel.physical_resource_id
            }
        ]

        self.environment.stacks = {"stack-name": mock_stack}
        response = self.environment.describe_resources()
        assert response == {
            "stack-name": [
                {
                    "LogicalResourceId": sentinel.logical_resource_id,
                    "PhysicalResourceId": sentinel.physical_resource_id
                }
            ]
        }

    def test_describe_resources_ignores_stack_does_not_exist_exception(self):
        mock_stack = Mock()
        mock_stack.full_stack_name = sentinel.full_stack_name
        mock_stack.describe_resources.side_effect = ClientError(
            {
                "Error": {
                    "Code": 500,
                    "Message": "stack does not exist"
                }
            },
            sentinel.operation
        )

        self.environment.stacks = {"name": mock_stack}
        response = self.environment.describe_resources()
        assert response == {}

    def test_describe_resources_raises_other_client_errors(self):
        mock_stack = Mock()
        mock_stack.full_stack_name = sentinel.full_stack_name
        mock_stack.describe_resources.side_effect = ClientError(
            {
                "Error": {
                    "Code": 500,
                    "Message": "Boom!"
                }
            },
            sentinel.operation
        )

        self.environment.stacks = {"mock_stack": mock_stack}
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
        mock_stack = Mock()
        mock_stack.name = "name"

        self.environment.stacks = {"mock_stack": mock_stack}

        mock_Event.return_value = sentinel.event

        response = self.environment._get_threading_events()
        assert response == {
            "name": sentinel.event
        }

    def test_get_initial_statuses(self):
        mock_stack = Mock()
        mock_stack.name = "name"

        self.environment.stacks = {"name": mock_stack}

        response = self.environment._get_initial_statuses()
        assert response == {
            "name": StackStatus.PENDING
        }

    def test_get_launch_dependencies(self):
        mock_stack = Mock()
        mock_stack.name = "dev/mock_stack"
        mock_stack.dependencies = [
            "dev/vpc",
            "dev/subnets",
            "prod/sg"
        ]

        self.environment.stacks = {"mock_stack": mock_stack}

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
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack2"]
        stack1.name = "stack1"
        stack2.dependencies = ["stack1"]
        stack2.name = "stack2"
        stacks = {
            "stack1": stack1,
            "stack2": stack2
        }
        self.environment.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.environment._check_for_circular_dependencies()
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
        stacks = {
            "stack1": stack1,
            "stack2": stack2,
            "stack3": stack3
        }
        self.environment.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.environment._check_for_circular_dependencies()
        assert all(x in str(ex) for x in ['stack3', 'stack2', 'stack1'])

    def test_no_circular_dependencies_throws_no_error(self):
        stack1 = MagicMock(Spec=Stack)
        stack2 = MagicMock(Spec=Stack)
        stack1.dependencies = ["stack2"]
        stack1.name = "stack1"
        stack2.dependencies = []
        stack2.name = "stack2"
        stacks = {
            "stack1": stack1,
            "stack2": stack2
        }
        self.environment.stacks = stacks
        # Check this runs without throwing an exception
        self.environment._check_for_circular_dependencies()

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
        stacks = {
            "stack1": stack1,
            "stack2": stack2,
            "stack3": stack3,
            "stack4": stack4
        }
        self.environment.stacks = stacks
        self.environment._check_for_circular_dependencies()

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
        stacks = {
            "stack1": stack1,
            "stack2": stack2,
            "stack3": stack3,
            "stack4": stack4,
            "stack5": stack5
        }
        self.environment.stacks = stacks
        self.environment._check_for_circular_dependencies()

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
        stacks = {
            "stack1": stack1,
            "stack2": stack2,
            "stack3": stack3,
            "stack4": stack4,
            "stack5": stack5
        }
        self.environment.stacks = stacks
        self.environment._check_for_circular_dependencies()

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
        stacks = {
            "stack1": stack1,
            "stack2": stack2,
            "stack3": stack3,
            "stack4": stack4
        }
        self.environment.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.environment._check_for_circular_dependencies()
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
        stacks = {
            "stack1": stack1,
            "stack2": stack2,
            "stack3": stack3,
            "stack4": stack4
        }
        self.environment.stacks = stacks
        with pytest.raises(CircularDependenciesError) as ex:
            self.environment._check_for_circular_dependencies()
        assert (all(x in str(ex) for x in ['stack4', 'stack3', 'stack2']) and
                'stack1' not in str(ex))

    @patch("sceptre.environment.Config")
    def test_get_config(self, mock_Config):
        mock_Config.return_value.read.return_value = {}

        self.environment.sceptre_dir = "sceptre_dir"
        self.environment.path = "environment_path"
        self.environment._options = {
            "cli_option": "value",
            "user_variables": sentinel.user_variables
        }

        self.environment._get_config()
        mock_Config.assert_called_once_with(
            sceptre_dir="sceptre_dir",
            environment_path="environment_path",
            base_file_name="config"
        )
        mock_Config.return_value.read.assert_called_once_with(
            sentinel.user_variables
        )

    def test_get_available_stacks(self):
        self.environment.path = os.path.join(
            "account", "environment", "region"
        )
        self.environment.sceptre_dir = os.path.join(
            os.getcwd(), "tests", "fixtures"
        )
        response = self.environment._get_available_stacks()
        assert sorted(response) == sorted([
            "account/environment/region/vpc",
            "account/environment/region/subnets",
            "account/environment/region/security_groups"
        ])

    @patch("sceptre.environment.Stack")
    @patch("sceptre.environment.Environment._get_available_stacks")
    @patch("sceptre.environment.ConnectionManager")
    @patch("sceptre.environment.Environment._get_config")
    def test_load_stacks(
            self, mock_get_config, mock_ConnectionManager,
            mock_get_available_stacks, mock_Stack
    ):
        mock_config = {
            "region": sentinel.region,
            "iam_role": sentinel.iam_role,
            "profile": sentinel.profile
        }
        mock_get_config.return_value = mock_config
        mock_ConnectionManager.return_value = sentinel.connection_manager
        mock_get_available_stacks.return_value = ["stack_name"]
        mock_Stack.return_value = sentinel.stack

        response = self.environment._load_stacks()

        # Check ConnectionManager() is called with correct arguments
        mock_ConnectionManager.assert_called_once_with(
            region=sentinel.region,
            iam_role=sentinel.iam_role,
            profile=sentinel.profile
        )

        # Check Stack() is called with correct arguments
        mock_Stack.assert_called_once_with(
            name="stack_name",
            environment_config=mock_config,
            connection_manager=sentinel.connection_manager
        )
        # Check _load_stacks() returns list of stacks
        assert response == {'stack_name': sentinel.stack}

    def test_get_available_environments(self):
        self.environment.path = "account"
        self.environment.sceptre_dir = os.path.join(
            os.getcwd(), "tests", "fixtures"
        )
        response = self.environment._get_available_environments()
        assert response == ["account/environment"]

    @patch("sceptre.environment.Environment")
    @patch("sceptre.environment.Environment._get_available_environments")
    def test_load_environments(
            self, mock_get_available_environments, mock_Environment
    ):
        mock_get_available_environments.return_value = ["env"]
        mock_Environment.return_value = sentinel.environment

        response = self.environment._load_environments()
        assert response == {"env": sentinel.environment}
