import logging
import yaml
import datetime
import os
import errno

from click.testing import CliRunner
from mock import MagicMock, patch, sentinel
import pytest

import sceptre.cli
from sceptre.cli import cli
from sceptre.config_reader import ConfigReader
from sceptre.environment import Environment
from sceptre.exceptions import SceptreException
from sceptre.stack import Stack
from sceptre.stack_status import StackStatus
from sceptre.stack_status import StackChangeSetStatus


class TestCli(object):

    def setup_method(self, test_method):
        self.patcher_ConfigReader = patch("sceptre.cli.ConfigReader")
        self.patcher_getcwd = patch("sceptre.cli.os.getcwd")

        self.mock_ConfigReader = self.patcher_ConfigReader.start()
        self.mock_getcwd = self.patcher_getcwd.start()

        self.mock_config_reader = MagicMock(spec=ConfigReader)
        self.mock_stack = MagicMock(spec=Stack)
        self.mock_environment = MagicMock(spec=Environment)
        self.mock_config_reader.construct_stack.return_value = self.mock_stack
        self.mock_config_reader.construct_environment.return_value = \
            self.mock_environment

        self.mock_ConfigReader.return_value = self.mock_config_reader
        self.mock_getcwd.return_value = sentinel.cwd

        self.runner = CliRunner()

    def teardown_method(self, test_method):
        self.patcher_ConfigReader.stop()
        self.patcher_getcwd.stop()

    @patch("sys.exit")
    def test_catch_excecptions(self, mock_exit):
            @sceptre.cli.catch_exceptions
            def raises_exception():
                raise SceptreException

            raises_exception()
            mock_exit.assert_called_once_with(1)

    def test_validate_template(self):
        self.runner.invoke(cli, ["validate-template", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.template.validate.assert_called_with()

    def test_generate_template(self):
        self.mock_stack.template.body = "body"
        result = self.runner.invoke(cli, ["generate-template", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )

        assert result.output == "body\n"

    def test_lock_stack(self):
        self.runner.invoke(cli, ["lock-stack", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
                "dev/vpc.yaml"
        )
        self.mock_stack.lock.assert_called_with()

    def test_unlock_stack(self):
        self.runner.invoke(cli, ["unlock-stack", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
                "dev/vpc.yaml"
        )
        self.mock_stack.unlock.assert_called_with()

    def test_describe_env_resources(self):
        self.mock_environment.describe_resources.return_value = {
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
        result = self.runner.invoke(cli, ["describe-env-resources", "dev"])
        self.mock_config_reader.construct_environment.assert_called_with("dev")
        self.mock_environment.describe_resources.assert_called_with()
        # Assert that there is output
        assert result.output

    def test_describe_stack_resources(self):
        self.mock_stack.describe_resources.return_value = {
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
        self.mock_config_reader.construct_stack.assert_called_with(
                "dev/vpc.yaml"
        )
        self.mock_stack.describe_resources.assert_called_with()
        # Assert that there is output.
        assert result.output

    def test_create_stack(self):
        self.runner.invoke(cli, ["create-stack", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
                "dev/vpc.yaml")
        self.mock_stack.create.assert_called_with()

    def test_delete_stack(self):
        self.runner.invoke(cli, ["delete-stack", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.delete.assert_called_with()

    def test_update_stack(self):
        self.runner.invoke(cli, ["update-stack", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.update.assert_called_with()

    def test_launch_stack(self):
        self.runner.invoke(cli, ["launch-stack", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.launch.assert_called_with()

    def test_launch_env(self):
        self.runner.invoke(cli, ["launch-env", "dev"])
        self.mock_config_reader.construct_environment.assert_called_with("dev")
        self.mock_environment.launch.assert_called_with()

    def test_launch_env_returns_zero_correctly(self):
        self.mock_environment.launch.return_value = dict(
            (sentinel.stack_name, StackStatus.COMPLETE) for _ in range(5)
        )
        result = self.runner.invoke(cli, ["launch-env", "environment"])
        assert result.exit_code == 0

    def test_launch_env_returns_non_zero_correctly(self):
        self.mock_environment.launch.return_value = dict(
            (sentinel.stack_name, StackStatus.FAILED) for _ in range(5)
        )
        result = self.runner.invoke(cli, ["launch-env", "environment"])
        assert result.exit_code == 1

    def test_delete_env(self):
        self.mock_environment.delete.return_value = sentinel.response
        self.runner.invoke(cli, ["delete-env", "dev"])
        self.mock_config_reader.construct_environment.assert_called_with("dev")
        self.mock_environment.delete.assert_called_with()

    def test_delete_env_returns_zero_correctly(self):
        self.mock_environment.delete.return_value = dict(
            (sentinel.stack_name, StackStatus.COMPLETE) for _ in range(5)
        )
        result = self.runner.invoke(cli, ["delete-env", "environment"])
        assert result.exit_code == 0

    def test_delete_env_returns_non_zero_correctly(self):
        self.mock_environment.delete.return_value = dict(
            (sentinel.stack_name, StackStatus.FAILED) for _ in range(5)
        )
        result = self.runner.invoke(cli, ["delete-env", "environment"])
        assert result.exit_code == 1

    def test_continue_update_rollback(self):
        self.runner.invoke(cli, ["continue-update-rollback", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.continue_update_rollback.assert_called_with()

    def test_create_change_set(self):
        self.runner.invoke(
            cli, ["create-change-set", "dev", "vpc", "cs1"]
        )
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.create_change_set.assert_called_with("cs1")

    def test_delete_change_set(self):
        self.runner.invoke(
            cli, ["delete-change-set", "dev", "vpc", "cs1"]
        )
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.delete_change_set.assert_called_with("cs1")

    def test_describe_change_set(self):
        self.mock_stack.describe_change_set.return_value = {
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
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.describe_change_set.assert_called_with("cs1")
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

    def test_describe_change_set_with_verbose_flag(self):
        self.mock_stack.describe_change_set.return_value = {
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
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.describe_change_set.assert_called_with("cs1")
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

    def test_execute_change_set(self):
        self.runner.invoke(cli, ["execute-change-set", "dev", "vpc", "cs1"])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.execute_change_set.assert_called_with("cs1")

    def test_list_change_sets(self):
        self.runner.invoke(cli, ["list-change-sets", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.list_change_sets.assert_called_with()

    @patch("sceptre.cli.uuid1")
    def test_update_with_change_set_with_input_yes(self, mock_uuid1):
        self.mock_stack.wait_for_cs_completion.return_value = \
            StackChangeSetStatus.READY
        self.mock_stack.describe_change_set.return_value = "description"
        mock_uuid1().hex = "1"
        self.runner.invoke(
            cli, ["update-stack-cs", "dev", "vpc", "--verbose"], input="y"
        )
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.create_change_set.assert_called_with("change-set-1")
        self.mock_stack.wait_for_cs_completion\
            .assert_called_with("change-set-1")
        self.mock_stack.execute_change_set.assert_called_with("change-set-1")

    @patch("sceptre.cli._simplify_change_set_description")
    @patch("sceptre.cli.uuid1")
    def test_update_with_change_set_without_verbose_flag(
            self, mock_uuid1, mock_simplify_change_set_description
    ):
        self.mock_stack.wait_for_cs_completion.return_value = \
            StackChangeSetStatus.READY
        self.mock_stack.describe_change_set.return_value = "description"
        mock_simplify_change_set_description.return_value = \
            "simplified_description"
        mock_uuid1().hex = "1"
        response = self.runner.invoke(
            cli, ["update-stack-cs", "dev", "vpc"], input="y"
        )
        assert "simplified_description" in response.output

    @patch("sceptre.cli.uuid1")
    def test_update_with_change_set_with_input_no(self, mock_uuid1):
        self.mock_stack.wait_for_cs_completion.return_value = \
            StackChangeSetStatus.READY
        self.mock_stack.describe_change_set.return_value = "description"
        mock_uuid1().hex = "1"
        self.runner.invoke(
            cli, ["update-stack-cs", "dev", "vpc", "--verbose"], input="n"
        )
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.create_change_set.assert_called_with("change-set-1")
        self.mock_stack.wait_for_cs_completion\
            .assert_called_with("change-set-1")
        self.mock_stack.delete_change_set.assert_called_with("change-set-1")

    @patch("sceptre.cli.uuid1")
    def test_update_with_change_set_with_status_defunct(self, mock_uuid1):
        self.mock_stack.wait_for_cs_completion.return_value = \
            StackChangeSetStatus.DEFUNCT
        self.mock_stack.describe_change_set.return_value = "description"
        mock_uuid1().hex = "1"
        result = self.runner.invoke(
            cli, ["update-stack-cs", "dev", "vpc", "--verbose"]
        )
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.create_change_set.assert_called_with("change-set-1")
        self.mock_stack.wait_for_cs_completion\
            .assert_called_with("change-set-1")
        assert result.exit_code == 1

    def test_describe_stack_outputs(self):
        self.runner.invoke(cli, ["describe-stack-outputs", "dev", "vpc"])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.describe_outputs.assert_called_with()

    def test_describe_stack_outputs_handles_envvar_flag(self):
        self.mock_stack.describe_outputs\
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

    def test_describe_env(self):
        self.mock_environment.describe.return_value = {
            "stack": "status"
        }
        result = self.runner.invoke(cli, ["describe-env", "dev"])
        assert result.output == "stack: status\n\n"

    def test_set_stack_policy_with_file_flag(self):
        policy_file = "tests/fixtures/stack_policies/lock.json"
        self.runner.invoke(cli, [
            "set-stack-policy", "dev", "vpc",
            "--policy-file=" + policy_file
        ])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )
        self.mock_stack.set_policy.assert_called_with(policy_file)

    def test_get_stack_policy_with_existing_policy(self):
        self.mock_stack.get_policy.return_value = {"StackPolicyBody": "policy"}

        result = self.runner.invoke(cli, ["get-stack-policy", "dev", "vpc"])
        assert result.output == "policy\n"

    def test_get_stack_policy_without_existing_policy(self):
        self.mock_stack.get_policy.return_value = {}

        result = self.runner.invoke(cli, ["get-stack-policy", "dev", "vpc"])
        assert result.output == "{}\n"

    def test_init_project_non_existant(self):
        self.patcher_getcwd.stop()
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
            template_dir = os.path.join(sceptre_dir, "templates")
            region = "test-region"
            os.environ["AWS_DEFAULT_REGION"] = region
            defaults = {
                "project_code": "example",
                "region": region
            }

            result = self.runner.invoke(cli, ["init", "project", "example"])
            assert not result.exception
            assert os.path.isdir(config_dir)
            assert os.path.isdir(template_dir)

            with open(os.path.join(config_dir, "config.yaml")) as config_file:
                config = yaml.load(config_file)

            assert config == defaults
        self.patcher_getcwd.start()

    def test_init_project_already_exist(self):
        self.patcher_getcwd.stop()
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
            template_dir = os.path.join(sceptre_dir, "templates")
            existing_config = {"Test": "Test"}

            os.mkdir(sceptre_dir)
            os.mkdir(config_dir)
            os.mkdir(template_dir)

            config_filepath = os.path.join(config_dir, "config.yaml")
            with open(config_filepath, 'w') as config_file:
                yaml.dump(existing_config, config_file)

            result = self.runner.invoke(cli, ["init", "project", "example"])
            assert result.exit_code == 1
            assert result.output == 'Folder \"example\" already exists.\n'
            assert os.path.isdir(config_dir)
            assert os.path.isdir(template_dir)

            with open(os.path.join(config_dir, "config.yaml")) as config_file:
                config = yaml.load(config_file)
            assert existing_config == config
        self.patcher_getcwd.start()

    @pytest.mark.parametrize("environment,config_structure,stdin,result", [
        (
         "A",
         {"": {}},
         'y\nA\nA\n', {"project_code": "A", "region": "A"}
        ),
        (
         "A",
         {"": {"project_code": "top", "region": "top"}},
         'y\n\n\n', {}
        ),
        (
         "A",
         {"": {"project_code": "top", "region": "top"}},
         'y\nA\nA\n', {"project_code": "A", "region": "A"}
        ),
        (
         "A/A",
         {
            "": {"project_code": "top", "region": "top"},
            "A": {"project_code": "A", "region": "A"},
         },
         'y\nA/A\nA/A\n', {"project_code": "A/A", "region": "A/A"}
        ),
        (
         "A/A",
         {
            "": {"project_code": "top", "region": "top"},
            "A": {"project_code": "A", "region": "A"},
         },
         'y\nA\nA\n', {}
        )
    ])
    def test_init_environment(
        self, environment, config_structure, stdin, result
    ):
        self.patcher_getcwd.stop()
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
            os.makedirs(config_dir)

            env_dir = os.path.join(sceptre_dir, "config", environment)
            for env_path, config in config_structure.items():
                path = os.path.join(config_dir, env_path)
                try:
                    os.makedirs(path)
                except OSError as e:
                    if e.errno == errno.EEXIST and os.path.isdir(path):
                        pass
                    else:
                        raise

                filepath = os.path.join(path, "config.yaml")
                with open(filepath, 'w') as config_file:
                    yaml.safe_dump(
                        config, stream=config_file, default_flow_style=False
                    )

            os.chdir(sceptre_dir)

            cmd_result = self.runner.invoke(
                cli, ["init", "env", environment],
                input=stdin
            )

            if result:
                with open(os.path.join(env_dir, "config.yaml")) as config_file:
                    config = yaml.load(config_file)
                assert config == result
            else:
                assert cmd_result.output.endswith(
                    "No config.yaml file needed - covered by parent config.\n"
                )
            self.patcher_getcwd.start()

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
