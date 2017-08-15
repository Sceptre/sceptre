import logging
import yaml
import datetime
import os
from io import StringIO

from click.testing import CliRunner
from mock import Mock, patch, sentinel
import pytest

import sceptre.cli
from sceptre.cli import cli
from sceptre.exceptions import SceptreException
from sceptre.stack_status import StackStatus
from sceptre.stack_status import StackChangeSetStatus


class TestCli(object):

    def setup_method(self, test_method):
        self.runner = CliRunner()

    @patch("sys.exit")
    def test_catch_excecptions(self, mock_exit):
            @sceptre.cli.catch_exceptions
            def raises_exception():
                raise SceptreException

            raises_exception()
            mock_exit.assert_called_once_with(1)

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_validate_template(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["validate-template", "dev", "vpc"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].validate_template\
            .assert_called_with()

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_generate_template(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        result = self.runner.invoke(cli, ["generate-template", "dev", "vpc"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})

        assert result.output == "{0}\n".format(
            mock_get_env.return_value.stacks["vpc"].template.body
        )

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_lock_stack(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["lock-stack", "dev", "vpc"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].lock\
            .assert_called_with()

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_unlock_stack(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["unlock-stack", "dev", "vpc"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].unlock\
            .assert_called_with()

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_describe_env_resources(self, mock_get_env, mock_getcwd):
        mock_get_env.return_value.describe_resources.return_value = {
            "stack-name-1": {
                "StackResources": [
                    {
                        "LogicalResourceId": "logical-resource-id",
                        "PhysicalResourceId": "physical-resource-id"
                    }
                ]
            },
            "stack-name-2": {
                "StackResources": [
                    {
                        "LogicalResourceId": "logical-resource-id",
                        "PhysicalResourceId": "physical-resource-id"
                    }
                ]
            }
        }
        mock_getcwd.return_value = sentinel.cwd
        result = self.runner.invoke(cli, ["describe-env-resources", "dev"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.describe_resources\
            .assert_called_with()
        # Assert that there is output
        assert result.output

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_describe_stack_resources(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_env.return_value.stacks["vpc"].describe_resources\
            .return_value = {
                "StackResources": [
                    {
                        "LogicalResourceId": "logical-resource-id",
                        "PhysicalResourceId": "physical-resource-id"
                    }
                ]
            }
        result = self.runner.invoke(
            cli, ["describe-stack-resources", "dev", "vpc"]
        )
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].describe_resources\
            .assert_called_with()
        # Assert that there is output.
        assert result.output

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_create_stack(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["create-stack", "dev", "vpc"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].create\
            .assert_called_with()

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_delete_stack(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["delete-stack", "dev", "vpc"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].delete\
            .assert_called_with()

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_update_stack(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["update-stack", "dev", "vpc"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].update\
            .assert_called_with()

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_launch_stack(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["launch-stack", "dev", "vpc"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].launch\
            .assert_called_with()

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_launch_env(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["launch-env", "dev"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.launch.assert_called_with()

    @patch("sceptre.cli.get_env")
    def test_launch_env_returns_zero_correctly(self, mock_get_env):
        mock_get_env.return_value.launch.return_value = dict(
            (sentinel.stack_name, StackStatus.COMPLETE) for _ in range(5)
        )
        result = self.runner.invoke(cli, ["launch-env", "environment"])
        assert result.exit_code == 0

    @patch("sceptre.cli.get_env")
    def test_launch_env_returns_non_zero_correctly(self, mock_get_env):
        mock_get_env.return_value.launch.return_value = dict(
            (sentinel.stack_name, StackStatus.FAILED) for _ in range(5)
        )
        result = self.runner.invoke(cli, ["launch-env", "environment"])
        assert result.exit_code == 1

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_delete_env(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_env.return_value.delete.return_value = \
            sentinel.response
        self.runner.invoke(cli, ["delete-env", "dev"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.delete.assert_called_with()

    @patch("sceptre.cli.get_env")
    def test_delete_env_returns_zero_correctly(self, mock_get_env):
        mock_get_env.return_value.delete.return_value = dict(
            (sentinel.stack_name, StackStatus.COMPLETE) for _ in range(5)
        )
        result = self.runner.invoke(cli, ["delete-env", "environment"])
        assert result.exit_code == 0

    @patch("sceptre.cli.get_env")
    def test_delete_env_returns_non_zero_correctly(self, mock_get_env):
        mock_get_env.return_value.delete.return_value = dict(
            (sentinel.stack_name, StackStatus.FAILED) for _ in range(5)
        )
        result = self.runner.invoke(cli, ["delete-env", "environment"])
        assert result.exit_code == 1

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_continue_update_rollback(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["continue-update-rollback", "dev", "vpc"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].\
            continue_update_rollback.assert_called_with()

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_create_change_set(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(
            cli, ["create-change-set", "dev", "vpc", "cs1"]
        )
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].create_change_set\
            .assert_called_with("cs1")

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_delete_change_set(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(
            cli, ["delete-change-set", "dev", "vpc", "cs1"]
        )
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].delete_change_set\
            .assert_called_with("cs1")

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_describe_change_set(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_env.return_value.stacks["vpc"].describe_change_set\
            .return_value = {
                "ChangeSetName": "change-set-1",
                "Changes": [
                    {
                        "ResourceChange": {
                            "ResourceType": "AWS::EC2::InternetGateway",
                            "Replacement": "True",
                            "PhysicalResourceId": "igw-04a59561",
                            "Details": [],
                            "Action": "Remove",
                            "Scope": [],
                            "LogicalResourceId": "InternetGateway"
                        }
                    }
                ],
                "CreationTime": "2017-01-20 14:10:25.239000+00:00",
                "ExecutionStatus": "AVAILABLE",
                "StackName": "example-dev-vpc",
                "Status": "CREATE_COMPLETE"
            }
        result = self.runner.invoke(
            cli, ["describe-change-set", "dev", "vpc", "cs1"]
        )
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].describe_change_set\
            .assert_called_with("cs1")
        assert yaml.safe_load(result.output) == {
            "ChangeSetName": "change-set-1",
            "Changes": [
                {
                    "ResourceChange": {
                        "ResourceType": "AWS::EC2::InternetGateway",
                        "Replacement": "True",
                        "PhysicalResourceId": "igw-04a59561",
                        "Action": "Remove",
                        "LogicalResourceId": "InternetGateway",
                        "Scope": []
                    }
                }
            ],
            "CreationTime": "2017-01-20 14:10:25.239000+00:00",
            "ExecutionStatus": "AVAILABLE",
            "StackName": "example-dev-vpc",
            "Status": "CREATE_COMPLETE"
        }

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_describe_change_set_with_verbose_flag(
        self, mock_get_env, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_env.return_value.stacks["vpc"].describe_change_set\
            .return_value = {
                "Changes": [
                    {
                        "ResourceChange": {
                            "ResourceType": "AWS::EC2::InternetGateway",
                            "PhysicalResourceId": "igw-04a59561",
                            "Details": [],
                            "Action": "Remove",
                            "Scope": [],
                            "LogicalResourceId": "InternetGateway"
                            }
                        }
                    ]
                }
        result = self.runner.invoke(
            cli, ["describe-change-set", "--verbose", "dev", "vpc", "cs1"]
        )
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].describe_change_set\
            .assert_called_with("cs1")
        assert yaml.safe_load(result.output) == {
            "Changes": [
                {
                    "ResourceChange": {
                        "ResourceType": "AWS::EC2::InternetGateway",
                        "PhysicalResourceId": "igw-04a59561",
                        "Details": [],
                        "Action": "Remove",
                        "Scope": [],
                        "LogicalResourceId": "InternetGateway"
                        }
                    }
                ]
        }

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_execute_change_set(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["execute-change-set", "dev", "vpc", "cs1"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].execute_change_set\
            .assert_called_with("cs1")

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_list_change_sets(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["list-change-sets", "dev", "vpc"])

        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].list_change_sets\
            .assert_called_with()

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.uuid1")
    @patch("sceptre.cli.get_env")
    def test_update_with_change_set_with_input_yes(
        self, mock_get_env, mock_uuid1, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_env.return_value.stacks["vpc"].wait_for_cs_completion\
            .return_value = StackChangeSetStatus.READY
        mock_get_env.return_value.stacks["vpc"].describe_change_set\
            .return_value = "description"
        mock_uuid1().hex = "1"
        self.runner.invoke(
            cli, ["update-stack-cs", "dev", "vpc", "--verbose"], input="y"
        )
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].create_change_set\
            .assert_called_with("change-set-1")
        mock_get_env.return_value.stacks["vpc"].wait_for_cs_completion\
            .assert_called_with("change-set-1")
        mock_get_env.return_value.stacks["vpc"].execute_change_set\
            .assert_called_with("change-set-1")

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli._simplify_change_set_description")
    @patch("sceptre.cli.uuid1")
    @patch("sceptre.cli.get_env")
    def test_update_with_change_set_without_verbose_flag(
            self, mock_get_environment, mock_uuid1,
            mock_simplify_change_set_description, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_environment.return_value.stacks["vpc"].wait_for_cs_completion\
            .return_value = StackChangeSetStatus.READY
        mock_get_environment.return_value.stacks["vpc"].describe_change_set\
            .return_value = "description"
        mock_simplify_change_set_description.return_value = \
            "simplified_description"
        mock_uuid1().hex = "1"
        response = self.runner.invoke(
            cli, ["update-stack-cs", "dev", "vpc"], input="y"
        )
        assert "simplified_description" in response.output

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.uuid1")
    @patch("sceptre.cli.get_env")
    def test_update_with_change_set_with_input_no(
        self, mock_get_env, mock_uuid1, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_env.return_value.stacks["vpc"].wait_for_cs_completion\
            .return_value = StackChangeSetStatus.READY
        mock_get_env.return_value.stacks["vpc"].describe_change_set\
            .return_value = "description"
        mock_uuid1().hex = "1"
        self.runner.invoke(
            cli, ["update-stack-cs", "dev", "vpc", "--verbose"], input="n"
        )
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].create_change_set\
            .assert_called_with("change-set-1")
        mock_get_env.return_value.stacks["vpc"].wait_for_cs_completion\
            .assert_called_with("change-set-1")
        mock_get_env.return_value.stacks["vpc"].delete_change_set\
            .assert_called_with("change-set-1")

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.uuid1")
    @patch("sceptre.cli.get_env")
    def test_update_with_change_set_with_status_defunct(
        self, mock_get_env, mock_uuid1, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        mock_get_env.return_value.stacks["vpc"].wait_for_cs_completion\
            .return_value = StackChangeSetStatus.DEFUNCT
        mock_get_env.return_value.stacks["vpc"].describe_change_set\
            .return_value = "description"
        mock_uuid1().hex = "1"
        result = self.runner.invoke(
            cli, ["update-stack-cs", "dev", "vpc", "--verbose"]
        )
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].create_change_set\
            .assert_called_with("change-set-1")
        mock_get_env.return_value.stacks["vpc"].wait_for_cs_completion\
            .assert_called_with("change-set-1")
        assert result.exit_code == 1

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_describe_stack_outputs(self, mock_get_env, mock_getcwd):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, ["describe-stack-outputs", "dev", "vpc"])
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value.stacks["vpc"].describe_outputs\
            .assert_called_with()

    @patch("sceptre.cli.get_env")
    def test_describe_stack_outputs_handles_envvar_flag(
            self, mock_get_env
    ):
        mock_get_env.return_value.stacks["vpc"].describe_outputs\
            .return_value = [
                {
                    "OutputKey": "key",
                    "OutputValue": "value"
                }
            ]
        result = self.runner.invoke(
            cli, ["describe-stack-outputs", "--export=envvar", "dev", "vpc"]
        )
        assert result.output == "export SCEPTRE_key=value\n"

    @patch("sceptre.cli.get_env")
    def test_describe_env(self, mock_get_env):
        mock_Environment = Mock()
        mock_Environment.describe.return_value = {"stack": "status"}
        mock_get_env.return_value = mock_Environment

        result = self.runner.invoke(cli, ["describe-env", "dev"])
        assert result.output == "stack: status\n\n"

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.get_env")
    def test_set_stack_policy_with_file_flag(
        self, mock_get_env, mock_getcwd
    ):
        mock_getcwd.return_value = sentinel.cwd
        self.runner.invoke(cli, [
            "set-stack-policy", "dev", "vpc",
            "--policy-file=tests/fixtures/stack_policies/lock.json"
        ])
        mock_Environment = Mock()
        mock_get_env.assert_called_with(sentinel.cwd, "dev", {})
        mock_get_env.return_value = mock_Environment

    @patch("sceptre.cli.get_env")
    def test_get_stack_policy_with_existing_policy(self, mock_get_env):
        mock_get_env.return_value.stacks["vpc"].get_policy\
            .return_value = {
                "StackPolicyBody": "policy"
            }

        result = self.runner.invoke(cli, ["get-stack-policy", "dev", "vpc"])
        assert result.output == "policy\n"

    @patch("sceptre.cli.get_env")
    def test_get_stack_policy_without_existing_policy(
            self, mock_get_env
    ):
        mock_get_env.return_value.stacks["vpc"].get_policy\
            .return_value = {}

        result = self.runner.invoke(cli, ["get-stack-policy", "dev", "vpc"])
        assert result.output == "{}\n"

    @patch("sceptre.cli.os.getcwd")
    @patch("sceptre.cli.Environment")
    def test_get_env(self, mock_Environment, mock_getcwd):
        mock_Environment.return_value = sentinel.environment
        mock_getcwd.return_value = sentinel.cwd
        response = sceptre.cli.get_env(
            sentinel.cwd, sentinel.environment_path, sentinel.options
        )
        mock_Environment.assert_called_once_with(
            sceptre_dir=sentinel.cwd,
            environment_path=sentinel.environment_path,
            options=sentinel.options
        )
        assert response == sentinel.environment

    @patch("sceptre.cli.click.prompt")
    def test_create_config_file_without_defaults(self, mock_prompt):
        mock_prompt.return_value = "test"
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')
            environment_path = os.path.join(config_dir, "env")
            os.makedirs(environment_path)
            sceptre.cli.create_config_file(config_dir, environment_path)

            config_filepath = os.path.join(environment_path, "config.yaml")
            assert os.path.isfile(config_filepath)
            with open(config_filepath) as config_file:
                contents = yaml.safe_load(config_file)
            assert contents == {"project_code": "test", "region": "test"}

    def test_create_config_file_with_defaults(self):
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')
            environment_path = os.path.join(config_dir, "env")
            os.makedirs(environment_path)
            defaults = {"project_code": "test", "region": "test"}
            with patch("sys.stdin", StringIO(u'\n\n')):
                sceptre.cli.create_config_file(
                    config_dir, environment_path, defaults
                )

            config_filepath = os.path.join(environment_path, "config.yaml")
            assert os.path.isfile(config_filepath)
            with open(config_filepath) as config_file:
                contents = yaml.safe_load(config_file)
            assert contents == {"project_code": "test", "region": "test"}

    @patch("sceptre.cli.get_nested_config")
    def test_create_config_file_with_defaults_and_nested_config(
        self, mock_get_nested_config
    ):
        mock_get_nested_config.return_value = {
            "project_code": "nested_config",
            "region": "nested_config",
        }
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')
            environment_path = os.path.join(config_dir, "env")
            os.makedirs(environment_path)
            defaults = {"project_code": "default", "region": "default"}

            with patch("sys.stdin", StringIO(u'\n\n')):
                sceptre.cli.create_config_file(
                    config_dir, environment_path, defaults
                )

            config_filepath = os.path.join(environment_path, "config.yaml")
            assert os.path.isfile(config_filepath)
            with open(config_filepath) as config_file:
                contents = yaml.safe_load(config_file)
            assert contents == {"project_code": "default", "region": "default"}

    @patch("sceptre.cli.get_nested_config")
    def test_create_config_file_with_defaults_and_extra_nested_config(
        self, mock_get_nested_config
    ):
        mock_get_nested_config.return_value = {
            "project_code": "nested_config",
            "region": "nested_config",
            "template_bucket_name": "nested_config"
        }
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')
            environment_path = os.path.join(config_dir, "env")
            os.makedirs(environment_path)
            defaults = {"project_code": "default", "region": "default"}

            with patch("sys.stdin", StringIO(u'\n\n\n')):
                sceptre.cli.create_config_file(
                    config_dir, environment_path, defaults
                )

            config_filepath = os.path.join(environment_path, "config.yaml")
            assert os.path.isfile(config_filepath)
            with open(config_filepath) as config_file:
                contents = yaml.safe_load(config_file)
            assert contents == {
                "project_code": "default",
                "region": "default"
            }

    @patch("sceptre.cli.get_nested_config")
    def test_create_config_file_with_defaults_and_input_not_in_nested_config(
        self, mock_get_nested_config
    ):
        mock_get_nested_config.return_value = {
            "project_code": "nested_config",
            "region": "nested_config",
            "template_bucket_name": "nested_config"
        }
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')
            environment_path = os.path.join(config_dir, "env")
            os.makedirs(environment_path)
            defaults = {"project_code": "default", "region": "default"}

            with patch("sys.stdin", StringIO(u'\ninput\n\n')):
                sceptre.cli.create_config_file(
                    config_dir, environment_path, defaults
                )

            config_filepath = os.path.join(environment_path, "config.yaml")
            assert os.path.isfile(config_filepath)
            with open(config_filepath) as config_file:
                contents = yaml.safe_load(config_file)
            assert contents == {
                "project_code": "default",
                "region": "default",
                "template_bucket_name": "input"
            }

    @patch("sceptre.cli.get_nested_config")
    def test_create_config_file_overwriting_defaults_and_nested_config(
        self, mock_get_nested_config
    ):
        mock_get_nested_config.return_value = {
            "project_code": "nested_config",
            "region": "nested_config",
            "template_bucket_name": "nested_config"
        }
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')
            environment_path = os.path.join(config_dir, "env")
            os.makedirs(environment_path)
            defaults = {"project_code": "default", "region": "default"}

            with patch("sys.stdin", StringIO(u'input\ninput\ninput\n')):
                sceptre.cli.create_config_file(
                    config_dir, environment_path, defaults
                )

            config_filepath = os.path.join(environment_path, "config.yaml")
            assert os.path.isfile(config_filepath)
            with open(config_filepath) as config_file:
                contents = yaml.safe_load(config_file)
            assert contents == {
                "project_code": "input",
                "region": "input",
                "template_bucket_name": "input"
            }

    @pytest.mark.parametrize("config_structure,result", [
        ({
            "A/A": {"project_code": "A/A", "region": "A/A"},
            "A": {"project_code": "A", "region": "A"},
            "A/B": {"project_code": "A/B", "region": "A/B"},
            "B": {"project_code": "B", "region": "B"},
        }, {
            "project_code": "A/A",
            "region": "A/A"
        }
        ),
        ({
            "A": {"project_code": "A", "region": "A"},
            "A/B": {"project_code": "A/B", "region": "A/B"},
            "B": {"project_code": "B", "region": "B"},
        }, {
            "project_code": "A",
            "region": "A"
        }
        ),
        ({
            "A/A": {"project_code": "A/A", "region": "A/A"},
            "A/B": {"project_code": "A/B", "region": "A/B"},
            "B": {"project_code": "B", "region": "B"},
        }, {
            "project_code": "A/A",
            "region": "A/A"
        }
        ),
        ({
            "A/A": {"project_code": "A/A"},
            "A": {"project_code": "A", "region": "A"},
            "A/B": {"project_code": "A/B", "region": "A/B"},
            "B": {"project_code": "B", "region": "B"},
        }, {
            "project_code": "A/A",
            "region": "A"
        }
        )
    ])
    def test_get_nested_config(self, config_structure, result):
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')

            for path, config in config_structure.items():
                os.makedirs(os.path.join(config_dir, path))
                filepath = os.path.join(config_dir, path, "config.yaml")
                with open(filepath, 'w') as config_file:
                    yaml.safe_dump(
                        config, stream=config_file, default_flow_style=False
                    )

            environment_path = os.path.join(config_dir, "A/A")
            nested_config = sceptre.cli.get_nested_config(
                config_dir, environment_path
            )
            assert nested_config == result

    @patch("sceptre.cli.create_config_file")
    def test_create_new_environment_without_existing(
        self, mock_create_config_file
    ):
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')
            folder_path = os.path.abspath('./project/config/A/A/A')
            new_path = "A/A/A"
            with patch("sys.stdin", StringIO(u'y\n')):
                sceptre.cli.create_new_environment(config_dir, new_path)

            assert os.path.isdir(folder_path)
            mock_create_config_file.assert_called_once_with(
                config_dir, folder_path
            )

    @patch("sceptre.cli.create_config_file")
    def test_create_new_environment_without_existing_no_confirm(
        self, mock_create_config_file
    ):
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')
            folder_path = os.path.abspath('./project/config/A/A/A')
            new_path = "A/A/A"
            with patch("sys.stdin", StringIO(u'n\n')):
                sceptre.cli.create_new_environment(config_dir, new_path)

            assert os.path.isdir(folder_path)
            mock_create_config_file.assert_not_called()

    @patch("sceptre.cli.create_config_file")
    def test_create_new_environment_with_existing(
        self, mock_create_config_file
    ):
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')
            folder_path = os.path.abspath('./project/config/A/A/A')
            os.makedirs(folder_path)
            new_path = "A/A/A"
            with patch("sys.stdin", StringIO(u'y\n')):
                sceptre.cli.create_new_environment(config_dir, new_path)

            assert os.path.isdir(folder_path)
            mock_create_config_file.assert_called_once_with(
                config_dir, folder_path
            )

    @patch("sceptre.cli.create_config_file")
    def test_create_new_environment_with_existing_no_confirm(
        self, mock_create_config_file
    ):
        with self.runner.isolated_filesystem():
            config_dir = os.path.abspath('./project/config')
            folder_path = os.path.abspath('./project/config/A/A/A')
            os.makedirs(folder_path)
            new_path = "A/A/A"
            with patch("sys.stdin", StringIO(u'n\n')):
                sceptre.cli.create_new_environment(config_dir, new_path)

            assert os.path.isdir(folder_path)
            mock_create_config_file.assert_not_called()

    @patch("sceptre.cli.create_config_file")
    def test_init_project(self, mock_create_config_file):
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
            defaults = {
                "project_code": "example",
                "region": os.environ.get("AWS_DEFAULT_REGION", "")
            }

            self.runner.invoke(cli, ["init", "project", "example"])

            assert os.path.isdir(sceptre_dir)
            mock_create_config_file.assert_called_once_with(
                config_dir, config_dir, defaults
            )

    @patch("sceptre.cli.create_new_environment")
    def test_init_environment(self, mock_create_new_environment):
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
            os.makedirs(config_dir)

            os.chdir(sceptre_dir)
            new_env = "example"

            self.runner.invoke(cli, ["init", "env", new_env])

            assert os.path.isdir(sceptre_dir)
            mock_create_new_environment.assert_called_once_with(
                config_dir, "example"
            )

    def test_setup_logging_with_debug(self):
        logger = sceptre.cli.setup_logging(True, False)
        assert logger.getEffectiveLevel() == logging.DEBUG
        assert logging.getLogger("botocore").getEffectiveLevel() == \
            logging.INFO

        # Silence logging for the rest of the tests
        logger.setLevel(logging.CRITICAL)

    def test_setup_logging_without_debug(self):
        logger = sceptre.cli.setup_logging(False, False)
        assert logger.getEffectiveLevel() == logging.INFO
        assert logging.getLogger("botocore").getEffectiveLevel() == \
            logging.CRITICAL

        # Silence logging for the rest of the tests
        logger.setLevel(logging.CRITICAL)

    @patch("sceptre.cli.click.echo")
    def test_write_with_yaml_format(self, mock_echo):
        sceptre.cli.write({"key": "value"}, "yaml")
        mock_echo.assert_called_once_with("key: value\n")

    @patch("sceptre.cli.click.echo")
    def test_write_with_json_format(self, mock_echo):
        sceptre.cli.write({"key": "value"}, "json")
        mock_echo.assert_called_once_with('{"key": "value"}')

    @patch("sceptre.cli.click.echo")
    def test_write_status_with_colour(self, mock_echo):
        sceptre.cli.write("stack: CREATE_COMPLETE", no_colour=False)
        mock_echo.assert_called_once_with(
            "stack: \x1b[32mCREATE_COMPLETE\x1b[0m"
        )

    @patch("sceptre.cli.click.echo")
    def test_write_status_without_colour(self, mock_echo):
        sceptre.cli.write("stack: CREATE_COMPLETE", no_colour=True)
        mock_echo.assert_called_once_with("stack: CREATE_COMPLETE")

    @patch("sceptre.cli.StackStatusColourer.colour")
    @patch("sceptre.cli.Formatter.format")
    def test_ColouredFormatter_format_with_string(
            self, mock_format, mock_colour
    ):
        mock_format.return_value = sentinel.response
        mock_colour.return_value = sentinel.coloured_response
        coloured_formatter = sceptre.cli.ColouredFormatter()
        response = coloured_formatter.format("string")
        mock_format.assert_called_once_with("string")
        mock_colour.assert_called_once_with(sentinel.response)
        assert response == sentinel.coloured_response

    def test_CustomJsonEncoder_with_non_json_serialisable_object(self):
        encoder = sceptre.cli.CustomJsonEncoder()
        response = encoder.encode(datetime.datetime(2016, 5, 3))
        assert response == '"2016-05-03 00:00:00"'
