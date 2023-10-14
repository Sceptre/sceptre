# -*- coding: utf-8 -*-

import pytest
from unittest.mock import MagicMock, patch, sentinel

from sceptre.exceptions import DependencyStackMissingOutputError
from sceptre.exceptions import StackDoesNotExistError
from botocore.exceptions import ClientError

from sceptre.connection_manager import ConnectionManager
from sceptre.resolvers.stack_output import (
    StackOutput,
    StackOutputExternal,
    StackOutputBase,
)
from sceptre.stack import Stack


class TestStackOutputResolver(object):
    def setup_method(self, method):
        self.stack = MagicMock(
            spec=Stack,
            dependencies=[],
            project_code="project-code",
            is_project_dependency=False,
            _connection_manager=MagicMock(spec=ConnectionManager),
        )
        self.stack.name = "my/stack"

    @patch("sceptre.resolvers.stack_output.StackOutput._get_output_value")
    def test_resolver(self, mock_get_output_value):
        dependency = MagicMock()
        dependency.project_code = "meh"
        dependency.name = "account/dev/vpc"
        dependency.profile = "dependency_profile"
        dependency.region = "dependency_region"
        dependency.sceptre_role = "dependency_sceptre_role"

        mock_get_output_value.return_value = "output_value"

        stack_output_resolver = StackOutput("account/dev/vpc.yaml::VpcId", self.stack)

        stack_output_resolver.setup()
        assert self.stack.dependencies == ["account/dev/vpc.yaml"]

        self.stack.dependencies = [dependency]
        result = stack_output_resolver.resolve()
        assert result == "output_value"
        mock_get_output_value.assert_called_once_with(
            "meh-account-dev-vpc",
            "VpcId",
            profile="dependency_profile",
            region="dependency_region",
            sceptre_role="dependency_sceptre_role",
        )

    @patch("sceptre.resolvers.stack_output.StackOutput._get_output_value")
    def test_resolver_with_existing_dependencies(self, mock_get_output_value):
        self.stack.dependencies = ["existing"]

        dependency = MagicMock()
        dependency.project_code = "meh"
        dependency.name = "account/dev/vpc"
        dependency.profile = "dependency_profile"
        dependency.region = "dependency_region"
        dependency.sceptre_role = "dependency_sceptre_role"

        mock_get_output_value.return_value = "output_value"

        stack_output_resolver = StackOutput("account/dev/vpc.yaml::VpcId", self.stack)

        stack_output_resolver.setup()
        assert self.stack.dependencies == ["existing", "account/dev/vpc.yaml"]

        self.stack.dependencies = [MagicMock(), dependency]
        result = stack_output_resolver.resolve()
        assert result == "output_value"
        mock_get_output_value.assert_called_once_with(
            "meh-account-dev-vpc",
            "VpcId",
            profile="dependency_profile",
            region="dependency_region",
            sceptre_role="dependency_sceptre_role",
        )

    @patch("sceptre.resolvers.stack_output.StackOutput._get_output_value")
    def test_resolve_with_implicit_stack_reference(self, mock_get_output_value):
        self.stack.name = "account/dev/stack"

        dependency = MagicMock()
        dependency.project_code = "meh"
        dependency.name = "account/dev/vpc"
        dependency.profile = "dependency_profile"
        dependency.region = "dependency_region"
        dependency.sceptre_role = "dependency_sceptre_role"

        mock_get_output_value.return_value = "output_value"

        stack_output_resolver = StackOutput("account/dev/vpc.yaml::VpcId", self.stack)

        stack_output_resolver.setup()
        assert self.stack.dependencies == ["account/dev/vpc.yaml"]

        self.stack.dependencies = [dependency]
        result = stack_output_resolver.resolve()
        assert result == "output_value"
        mock_get_output_value.assert_called_once_with(
            "meh-account-dev-vpc",
            "VpcId",
            profile="dependency_profile",
            region="dependency_region",
            sceptre_role="dependency_sceptre_role",
        )

    @patch("sceptre.resolvers.stack_output.StackOutput._get_output_value")
    def test_resolve_with_implicit_stack_reference_top_level(
        self, mock_get_output_value
    ):
        dependency = MagicMock()
        dependency.project_code = "meh"
        dependency.name = "vpc"
        dependency.profile = "dependency_profile"
        dependency.region = "dependency_region"
        dependency.sceptre_role = "dependency_sceptre_role"

        mock_get_output_value.return_value = "output_value"

        stack_output_resolver = StackOutput("vpc.yaml::VpcId", self.stack)

        stack_output_resolver.setup()
        assert self.stack.dependencies == ["vpc.yaml"]

        self.stack.dependencies = [dependency]
        result = stack_output_resolver.resolve()
        assert result == "output_value"
        mock_get_output_value.assert_called_once_with(
            "meh-vpc",
            "VpcId",
            profile="dependency_profile",
            region="dependency_region",
            sceptre_role="dependency_sceptre_role",
        )

    def test_setup__stack_is_project_dependency__does_not_add_dependency(self):
        self.stack.is_project_dependency = True
        stack_output_resolver = StackOutput("vpc.yaml::VpcId", self.stack)
        stack_output_resolver.setup()
        assert self.stack.dependencies == []

    def test_resolve__stack_is_project_dependency__returns_none(self):
        self.stack.is_project_dependency = True
        stack_output_resolver = StackOutput("vpc.yaml::VpcId", self.stack)
        resolved = stack_output_resolver.resolve()
        assert resolved is None

    @patch("sceptre.resolvers.stack_output.StackOutput._get_output_value")
    def test_resolve__stack_is_project_dependency__does_not_request_stack_outputs(
        self, mock_get_output_value
    ):
        self.stack.is_project_dependency = True
        stack_output_resolver = StackOutput("vpc.yaml::VpcId", self.stack)
        stack_output_resolver.resolve()
        mock_get_output_value.assert_not_called()


class TestStackOutputExternalResolver(object):
    @patch("sceptre.resolvers.stack_output.StackOutputExternal._get_output_value")
    def test_resolve(self, mock_get_output_value):
        stack = MagicMock(spec=Stack)
        stack.name = "my/stack"
        stack.dependencies = []
        stack._connection_manager = MagicMock(spec=ConnectionManager)
        stack_output_external_resolver = StackOutputExternal(
            "another/account-vpc::VpcId", stack
        )
        mock_get_output_value.return_value = "output_value"
        stack_output_external_resolver.resolve()
        mock_get_output_value.assert_called_once_with(
            "another/account-vpc", "VpcId", None, None, None
        )
        assert stack.dependencies == []

    @patch("sceptre.resolvers.stack_output.StackOutputExternal._get_output_value")
    def test_resolve_with_args(self, mock_get_output_value):
        stack = MagicMock(spec=Stack)
        stack.name = "my/stack"
        stack.dependencies = []
        stack._connection_manager = MagicMock(spec=ConnectionManager)
        stack_output_external_resolver = StackOutputExternal(
            "another/account-vpc::VpcId region::profile::sceptre_role", stack
        )
        mock_get_output_value.return_value = "output_value"
        stack_output_external_resolver.resolve()
        mock_get_output_value.assert_called_once_with(
            "another/account-vpc", "VpcId", "region", "profile", "sceptre_role"
        )
        assert stack.dependencies == []


class MockStackOutputBase(StackOutputBase):
    """
    MockBaseResolver inherits from the abstract base class
    StackOutputBaseResolver, and implements the abstract methods. It is used
    to allow testing on StackOutputBaseResolver, which is not otherwise
    instantiable.
    """

    def __init__(self, *args, **kwargs):
        super(MockStackOutputBase, self).__init__(*args, **kwargs)

    def resolve(self):
        pass


class TestStackOutputBaseResolver(object):
    def setup_method(self, test_method):
        self.stack = MagicMock(spec=Stack)
        self.stack.name = "my/stack.yaml"
        self.stack._connection_manager = MagicMock(spec=ConnectionManager)
        self.base_stack_output_resolver = MockStackOutputBase(None, self.stack)

    @patch("sceptre.resolvers.stack_output.StackOutputBase._get_stack_outputs")
    def test_get_output_value_with_valid_key(self, mock_get_stack_outputs):
        mock_get_stack_outputs.return_value = {"key": "value"}

        response = self.base_stack_output_resolver._get_output_value(
            sentinel.stack_name, "key"
        )

        assert response == "value"

    @patch("sceptre.resolvers.stack_output.StackOutputBase._get_stack_outputs")
    def test_get_output_value_with_invalid_key(self, mock_get_stack_outputs):
        mock_get_stack_outputs.return_value = {"key": "value"}

        with pytest.raises(DependencyStackMissingOutputError):
            self.base_stack_output_resolver._get_output_value(
                sentinel.stack_name, "invalid_key"
            )

    def test_get_stack_outputs_with_valid_stack(self):
        self.stack.connection_manager.call.return_value = {
            "Stacks": [
                {
                    "Outputs": [
                        {
                            "OutputKey": "key_1",
                            "OutputValue": "value_1",
                            "Description": "description_1",
                        },
                        {
                            "OutputKey": "key_2",
                            "OutputValue": "value_2",
                            "Description": "description_2",
                        },
                    ]
                }
            ]
        }

        response = self.base_stack_output_resolver._get_stack_outputs(
            sentinel.stack_name
        )

        assert response == {"key_1": "value_1", "key_2": "value_2"}

    def test_get_stack_outputs_with_valid_stack_without_outputs(self):
        self.stack.connection_manager.call.return_value = {"Stacks": [{}]}

        response = self.base_stack_output_resolver._get_stack_outputs(
            sentinel.stack_name
        )
        assert response == {}

    def test_get_stack_outputs_with_unlaunched_stack(self):
        self.stack.connection_manager.call.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "stack does not exist"}},
            sentinel.operation,
        )

        with pytest.raises(StackDoesNotExistError):
            self.base_stack_output_resolver._get_stack_outputs(sentinel.stack_name)

    def test_get_stack_outputs_with_unkown_boto_error(self):
        self.stack.connection_manager.call.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Boom!"}}, sentinel.operation
        )

        with pytest.raises(ClientError):
            self.base_stack_output_resolver._get_stack_outputs(sentinel.stack_name)
