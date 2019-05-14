# -*- coding: utf-8 -*-

import pytest
from mock import MagicMock, patch, sentinel

from sceptre.exceptions import DependencyStackMissingOutputError
from sceptre.exceptions import StackDoesNotExistError
from botocore.exceptions import ClientError

from sceptre.connection_manager import ConnectionManager
from sceptre.resolvers.stack_output import \
    StackOutput, StackOutputExternal, StackOutputBase
from sceptre.stack import Stack


class TestStackOutputResolver(object):

    @patch(
        "sceptre.resolvers.stack_output.StackOutput._get_output_value"
    )
    def test_resolver(self, mock_get_output_value):
        stack = MagicMock(spec=Stack)
        stack.dependencies = []
        stack.project_code = "project-code"
        stack._connection_manager = MagicMock(spec=ConnectionManager)

        dependency = MagicMock()
        dependency.name = "account/dev/vpc"
        dependency.profile = 'dependency_profile'
        dependency.region = 'dependency_region'

        mock_get_output_value.return_value = "output_value"

        stack_output_resolver = StackOutput(
            "account/dev/vpc.yaml::VpcId", stack
        )

        stack_output_resolver.setup()
        assert stack.dependencies == ["account/dev/vpc.yaml"]

        stack.dependencies = [dependency]
        result = stack_output_resolver.resolve()
        assert result == "output_value"
        mock_get_output_value.assert_called_once_with(
            "project-code-account-dev-vpc", "VpcId",
            profile='dependency_profile', region='dependency_region'
        )

    @patch(
        "sceptre.resolvers.stack_output.StackOutput._get_output_value"
    )
    def test_resolver_with_existing_dependencies(self, mock_get_output_value):
        stack = MagicMock(spec=Stack)
        stack.dependencies = ["existing"]
        stack.project_code = "project-code"
        stack._connection_manager = MagicMock(spec=ConnectionManager)

        dependency = MagicMock()
        dependency.name = "account/dev/vpc"
        dependency.profile = 'dependency_profile'
        dependency.region = 'dependency_region'

        mock_get_output_value.return_value = "output_value"

        stack_output_resolver = StackOutput(
            "account/dev/vpc.yaml::VpcId", stack
        )

        stack_output_resolver.setup()
        assert stack.dependencies == ["existing", "account/dev/vpc.yaml"]

        stack.dependencies = [MagicMock(), dependency]
        result = stack_output_resolver.resolve()
        assert result == "output_value"
        mock_get_output_value.assert_called_once_with(
            "project-code-account-dev-vpc", "VpcId",
            profile='dependency_profile', region='dependency_region'
        )

    @patch(
        "sceptre.resolvers.stack_output.StackOutput._get_output_value"
    )
    def test_resolve_with_implicit_stack_reference(
        self, mock_get_output_value
    ):
        stack = MagicMock(spec=Stack)
        stack.dependencies = []
        stack.project_code = "project-code"
        stack.name = "account/dev/stack"
        stack._connection_manager = MagicMock(spec=ConnectionManager)

        dependency = MagicMock()
        dependency.name = "account/dev/vpc"
        dependency.profile = 'dependency_profile'
        dependency.region = 'dependency_region'

        mock_get_output_value.return_value = "output_value"

        stack_output_resolver = StackOutput("account/dev/vpc.yaml::VpcId", stack)

        stack_output_resolver.setup()
        assert stack.dependencies == ["account/dev/vpc.yaml"]

        stack.dependencies = [dependency]
        result = stack_output_resolver.resolve()
        assert result == "output_value"
        mock_get_output_value.assert_called_once_with(
            "project-code-account-dev-vpc", "VpcId",
            profile='dependency_profile', region='dependency_region'
        )

    @patch(
        "sceptre.resolvers.stack_output.StackOutput._get_output_value"
    )
    def test_resolve_with_implicit_stack_reference_top_level(
        self, mock_get_output_value
    ):
        stack = MagicMock(spec=Stack)
        stack.dependencies = []
        stack.project_code = "project-code"
        stack.name = "stack"
        stack._connection_manager = MagicMock(spec=ConnectionManager)

        dependency = MagicMock()
        dependency.name = "vpc"
        dependency.profile = 'dependency_profile'
        dependency.region = 'dependency_region'

        mock_get_output_value.return_value = "output_value"

        stack_output_resolver = StackOutput("vpc.yaml::VpcId", stack)

        stack_output_resolver.setup()
        assert stack.dependencies == ["vpc.yaml"]

        stack.dependencies = [dependency]
        result = stack_output_resolver.resolve()
        assert result == "output_value"
        mock_get_output_value.assert_called_once_with(
            "project-code-vpc", "VpcId",
            profile='dependency_profile', region='dependency_region'
        )


class TestStackOutputExternalResolver(object):

    @patch(
        "sceptre.resolvers.stack_output.StackOutputExternal._get_output_value"
    )
    def test_resolve(self, mock_get_output_value):
        stack = MagicMock(spec=Stack)
        stack.dependencies = []
        stack._connection_manager = MagicMock(spec=ConnectionManager)
        stack_output_external_resolver = StackOutputExternal(
            "another/account-vpc::VpcId", stack
        )
        mock_get_output_value.return_value = "output_value"
        stack_output_external_resolver.resolve()
        mock_get_output_value.assert_called_once_with(
            "another/account-vpc", "VpcId", None
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
        self.stack._connection_manager = MagicMock(
            spec=ConnectionManager
        )
        self.base_stack_output_resolver = MockStackOutputBase(
            None, self.stack
        )

    @patch(
        "sceptre.resolvers.stack_output.StackOutputBase._get_stack_outputs"
    )
    def test_get_output_value_with_valid_key(self, mock_get_stack_outputs):
        mock_get_stack_outputs.return_value = {"key": "value"}

        response = self.base_stack_output_resolver._get_output_value(
            sentinel.stack_name, "key"
        )

        assert response == "value"

    @patch(
        "sceptre.resolvers.stack_output.StackOutputBase._get_stack_outputs"
    )
    def test_get_output_value_with_invalid_key(self, mock_get_stack_outputs):
        mock_get_stack_outputs.return_value = {"key": "value"}

        with pytest.raises(DependencyStackMissingOutputError):
            self.base_stack_output_resolver._get_output_value(
                sentinel.stack_name, "invalid_key"
            )

    def test_get_stack_outputs_with_valid_stack(self):
        self.stack.connection_manager.call.return_value = {
            "Stacks": [{
                "Outputs": [
                    {
                        "OutputKey": "key_1",
                        "OutputValue": "value_1",
                        "Description": "description_1"
                    },
                    {
                        "OutputKey": "key_2",
                        "OutputValue": "value_2",
                        "Description": "description_2"
                    }
                ]
            }]
        }

        response = self.base_stack_output_resolver._get_stack_outputs(
            sentinel.stack_name
        )

        assert response == {
            "key_1": "value_1",
            "key_2": "value_2"
        }

    def test_get_stack_outputs_with_valid_stack_without_outputs(self):
        self.stack.connection_manager.call.return_value = {
            "Stacks": [{}]
        }

        response = self.base_stack_output_resolver._get_stack_outputs(
            sentinel.stack_name
        )
        assert response == {}

    def test_get_stack_outputs_with_unlaunched_stack(self):
        self.stack.connection_manager.call.side_effect = ClientError(
            {
                "Error": {
                    "Code": "404",
                    "Message": "stack does not exist"
                }
            },
            sentinel.operation
        )

        with pytest.raises(StackDoesNotExistError):
            self.base_stack_output_resolver._get_stack_outputs(
                sentinel.stack_name
            )

    def test_get_stack_outputs_with_unkown_boto_error(self):
        self.stack.connection_manager.call.side_effect = ClientError(
            {
                "Error": {
                    "Code": "500",
                    "Message": "Boom!"
                }
            },
            sentinel.operation
        )

        with pytest.raises(ClientError):
            self.base_stack_output_resolver._get_stack_outputs(
                sentinel.stack_name
            )
