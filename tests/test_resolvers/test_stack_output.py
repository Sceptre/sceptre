# -*- coding: utf-8 -*-

import pytest
from mock import MagicMock, Mock, patch, sentinel

from sceptre.config import Config
from sceptre.resolvers.stack_output import \
    StackOutput, StackOutputExternal, StackOutputBase
from sceptre.exceptions import DependencyStackMissingOutputError
from sceptre.exceptions import StackDoesNotExistError
from botocore.exceptions import ClientError


class TestStackOutputResolver(object):

    @patch(
        "sceptre.resolvers.stack_output.StackOutput._get_output_value"
    )
    def test_resolve(self, mock_get_output_value):
        mock_environment_config = MagicMock(spec=Config)
        mock_stack_config = MagicMock(spec=Config)
        mock_environment_config.__getitem__.return_value = "project-code"
        mock_stack_config.__getitem__.return_value = []

        stack_output_resolver = StackOutput(
            environment_config=mock_environment_config,
            stack_config=mock_stack_config,
            connection_manager=sentinel.connection_manager,
            argument="account/dev/vpc::VpcId"
        )

        mock_get_output_value.return_value = "output_value"

        stack_output_resolver.resolve()

        mock_get_output_value.assert_called_once_with(
            "project-code-account-dev-vpc", "VpcId"
        )

    @patch(
        "sceptre.resolvers.stack_output.StackOutput._get_output_value"
    )
    def test_resolve_with_implicit_stack_reference(
        self, mock_get_output_value
    ):
        mock_environment_config = MagicMock(spec=Config)
        mock_stack_config = MagicMock(spec=Config)
        mock_environment_config.__getitem__.return_value = "project-code"
        mock_stack_config.environment_path = "account/dev"
        mock_stack_config.__getitem__.return_value = []

        stack_output_resolver = StackOutput(
            environment_config=mock_environment_config,
            stack_config=mock_stack_config,
            connection_manager=sentinel.connection_manager,
            argument="vpc::VpcId"
        )

        mock_get_output_value.return_value = "output_value"

        stack_output_resolver.resolve()

        mock_get_output_value.assert_called_once_with(
            "project-code-account-dev-vpc", "VpcId"
        )


class TestStackOutputExternalResolver(object):

    def setup_method(self, test_method):
        self.stack_output_resolver = StackOutputExternal(
            environment_config=sentinel.environment_config,
            stack_config=sentinel.config,
            connection_manager=sentinel.connection_manager,
            argument=None
        )

    @patch(
        "sceptre.resolvers.stack_output.StackOutputExternal._get_output_value"
    )
    def test_resolve(self, mock_get_output_value):
        mock_environment_config = MagicMock(spec=Config)
        mock_environment_config.__getitem__.return_value = "project-code"
        mock_environment_config.environment_path = "account/dev"
        self.stack_output_resolver.environment_config = mock_environment_config
        self.stack_output_resolver.argument = "vpc::VpcId"

        mock_get_output_value.return_value = "output_value"

        self.stack_output_resolver.resolve()

        mock_get_output_value.assert_called_once_with(
            "vpc", "VpcId"
        )


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
        self.mock_base_stack_output_resolver = MockStackOutputBase(
            environment_config=sentinel.environment_config,
            stack_config=sentinel.config,
            connection_manager=sentinel.connection_manager,
            argument=None
        )

    @patch(
        "sceptre.resolvers.stack_output.StackOutputBase._get_stack_outputs"
    )
    def test_get_output_value_with_valid_key(self, mock_get_stack_outputs):
        mock_get_stack_outputs.return_value = {"key": "value"}

        response = self.mock_base_stack_output_resolver._get_output_value(
            sentinel.stack_name, "key"
        )

        assert response == "value"

    @patch(
        "sceptre.resolvers.stack_output.StackOutputBase._get_stack_outputs"
    )
    def test_get_output_value_with_invalid_key(self, mock_get_stack_outputs):
        mock_get_stack_outputs.return_value = {"key": "value"}

        with pytest.raises(DependencyStackMissingOutputError):
            self.mock_base_stack_output_resolver._get_output_value(
                sentinel.stack_name, "invalid_key"
            )

    def test_get_stack_outputs_with_valid_stack(self):
        mock_connection_manager = Mock()
        mock_connection_manager.call.return_value = {
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
        self.mock_base_stack_output_resolver.connection_manager = \
            mock_connection_manager

        response = self.mock_base_stack_output_resolver._get_stack_outputs(
            sentinel.stack_name
        )
        assert response == {
            "key_1": "value_1",
            "key_2": "value_2"
        }

    def test_get_stack_outputs_with_unlaunched_stack(self):
        mock_connection_manager = Mock()
        mock_connection_manager.call.side_effect = ClientError(
            {
                "Error": {
                    "Code": "404",
                    "Message": "stack does not exist"
                }
            },
            sentinel.operation
        )
        self.mock_base_stack_output_resolver.connection_manager = \
            mock_connection_manager

        with pytest.raises(StackDoesNotExistError):
            self.mock_base_stack_output_resolver._get_stack_outputs(
                sentinel.stack_name
            )

    def test_get_stack_outputs_with_unkown_boto_error(self):
        mock_connection_manager = Mock()
        mock_connection_manager.call.side_effect = ClientError(
            {
                "Error": {
                    "Code": "500",
                    "Message": "Boom!"
                }
            },
            sentinel.operation
        )
        self.mock_base_stack_output_resolver.connection_manager = \
            mock_connection_manager

        with pytest.raises(ClientError):
            self.mock_base_stack_output_resolver._get_stack_outputs(
                sentinel.stack_name
            )
