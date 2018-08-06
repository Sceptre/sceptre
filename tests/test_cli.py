import logging
import yaml
import datetime
import os
import errno
from uuid import UUID

from click.testing import CliRunner
from mock import MagicMock, patch, sentinel
import pytest
import click

from sceptre.cli import cli
from sceptre.config.reader import ConfigReader
from sceptre.stack import Stack
from sceptre.stack_group import StackGroup
from sceptre.stack_status import StackStatus, StackChangeSetStatus
from sceptre.cli.helpers import setup_logging, write, ColouredFormatter
from sceptre.cli.helpers import CustomJsonEncoder, catch_exceptions
from sceptre.cli.helpers import get_stack_or_stack_group
from botocore.exceptions import ClientError
from sceptre.exceptions import SceptreException


class TestCli(object):

    def setup_method(self, test_method):
        self.patcher_ConfigReader = patch("sceptre.cli.helpers.ConfigReader")
        self.patcher_getcwd = patch("sceptre.cli.os.getcwd")

        self.mock_ConfigReader = self.patcher_ConfigReader.start()
        self.mock_getcwd = self.patcher_getcwd.start()

        self.mock_config_reader = MagicMock(spec=ConfigReader)
        self.mock_stack = MagicMock(spec=Stack)
        self.mock_stack_group = MagicMock(spec=StackGroup)

        self.mock_config_reader.construct_stack.return_value = self.mock_stack
        self.mock_config_reader.construct_stack_group.return_value = \
            self.mock_stack_group

        self.mock_ConfigReader.return_value = self.mock_config_reader
        self.mock_getcwd.return_value = sentinel.cwd

        self.runner = CliRunner()

    def teardown_method(self, test_method):
        self.patcher_ConfigReader.stop()
        self.patcher_getcwd.stop()

    @patch("sys.exit")
    def test_catch_excecptions(self, mock_exit):
        @catch_exceptions
        def raises_exception():
            raise SceptreException()

        raises_exception()
        mock_exit.assert_called_once_with(1)

    @pytest.mark.parametrize("command,files,output", [
        # one --var option
        (
            ["--var", "a=1", "noop"],
            {},
            {"a": "1"}
        ),
        # multiple --var options
        (
            ["--var", "a=1", "--var", "b=2", "noop"],
            {},
            {"a": "1", "b": "2"}
        ),
        # one --var-file option
        (
            ["--var-file", "foo.yaml", "noop"],
            {
                "foo.yaml": {"key1": "val1", "key2": "val2"}
            },
            {"key1": "val1", "key2": "val2"}
        ),
        # multiple --var-file option
        (
            ["--var-file", "foo.yaml", "--var-file", "bar.yaml", "noop"],
            {
                "foo.yaml": {"key1": "parent_value1", "key2": "parent_value2"},
                "bar.yaml": {"key2": "child_value2", "key3": "child_value3"}
            },
            {
                "key1": "parent_value1",
                "key2": "child_value2",
                "key3": "child_value3"
            }
        ),
        # mix of --var and --var-file
        (
            ["--var-file", "foo.yaml", "--var", "key2=var2", "noop"],
            {
                "foo.yaml": {"key1": "file1", "key2": "file2"}
            },
            {"key1": "file1", "key2": "var2"}
        ),
    ])
    def test_user_variables(self, command, files, output):
        @cli.command()
        @click.pass_context
        def noop(ctx):
            click.echo(yaml.safe_dump(ctx.obj["user_variables"]))

        self.patcher_getcwd.stop()
        with self.runner.isolated_filesystem():
            for name, content in files.items():
                with open(name, "w") as fh:
                    yaml.safe_dump(content, fh)

            result = self.runner.invoke(cli, command)
        self.patcher_getcwd.start()

        user_variables = yaml.safe_load(result.output)
        assert result.exit_code == 0
        assert user_variables == output

    def test_validate_template_with_valid_template(self):
        self.mock_stack.template.validate.return_value = {
                    "Parameters": "Example",
                    "ResponseMetadata": {
                        "HTTPStatusCode": 200
                    }
                }
        result = self.runner.invoke(cli, ["validate", "dev/vpc.yaml"])
        self.mock_stack.template.validate.assert_called_with()

        assert result.output == "Template is valid. Template details:\n\n" \
            "Parameters: Example\n\n"

    def test_validate_template_with_invalid_template(self):
        client_error = ClientError(
            {
                "Errors":
                {
                    "Message": "Unrecognized resource types",
                    "Code": "ValidationError",
                }
            },
            "ValidateTemplate"
        )
        self.mock_stack.template.validate.side_effect = client_error

        expected_result = str(client_error) + "\n"
        result = self.runner.invoke(cli, ["validate", "dev/vpc.yaml"])
        assert result.output == expected_result

    def test_estimate_template_cost_with_browser(self):
        self.mock_stack.template.estimate_cost.return_value = {
                "Url": "http://example.com",
                "ResponseMetadata": {
                    "HTTPStatusCode": 200
                }
            }

        args = ["estimate-cost", "dev/vpc.yaml"]
        result = self.runner.invoke(cli, args)

        self.mock_stack.template.estimate_cost.assert_called_with()

        assert result.output == \
            '{0}{1}'.format("View the estimated cost at:\n",
                            "http://example.com\n\n")

    def test_estimate_template_cost_with_no_browser(self):
        client_error = ClientError(
            {
                "Errors":
                {
                    "Message": "No Browser",
                    "Code": "Error",
                }
            },
            "Webbrowser"
        )
        self.mock_stack.template.estimate_cost.side_effect = client_error

        expected_result = str(client_error) + "\n"
        result = self.runner.invoke(
                    cli,
                    ["estimate-cost", "dev/vpc.yaml"]
                )
        assert result.output == expected_result

    def test_generate_template(self):
        self.mock_stack.template.body = "body"
        result = self.runner.invoke(cli, ["generate", "dev/vpc.yaml"])
        self.mock_config_reader.construct_stack.assert_called_with(
            "dev/vpc.yaml"
        )

        assert result.output == "body\n"

    def test_lock_stack(self):
        self.runner.invoke(
            cli, ["set-policy", "dev/vpc.yaml", "-b", "deny-all"]
        )
        self.mock_config_reader.construct_stack.assert_called_with(
                "dev/vpc.yaml"
        )
        self.mock_stack.lock.assert_called_with()

    def test_unlock_stack(self):
        self.runner.invoke(
            cli, ["set-policy", "dev/vpc.yaml", "-b", "allow-all"]
        )
        self.mock_config_reader.construct_stack.assert_called_with(
                "dev/vpc.yaml"
        )
        self.mock_stack.unlock.assert_called_with()

    def test_set_policy_with_file_flag(self):
        policy_file = "tests/fixtures/stack_policies/lock.json"
        result = self.runner.invoke(cli, [
            "set-policy", "dev/vpc.yaml", policy_file
        ])
        assert result.exit_code == 0
        self.mock_stack.set_policy.assert_called_once_with(policy_file)

    def test_describe_policy_with_existing_policy(self):
        self.mock_stack.get_policy.return_value = {
            "StackPolicyBody": "Body"
        }

        result = self.runner.invoke(
            cli, ["describe", "policy", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert result.output == "Body\n"

    def test_list_group_resources(self):
        response = {
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
        self.mock_stack_group.describe_resources.return_value = response
        result = self.runner.invoke(cli, ["list", "resources", "dev"])
        assert yaml.load(result.output) == response
        assert result.exit_code == 0

    def test_list_stack_resources(self):
        response = {
                "StackResources": [
                    {
                        "LogicalResourceId": "logical-resource-id",
                        "PhysicalResourceId": "physical-resource-id"
                    }
                ]
            }
        self.mock_stack.describe_resources.return_value = response
        result = self.runner.invoke(cli, ["list", "resources", "dev/vpc.yaml"])
        assert yaml.load(result.output) == response
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "command,success,yes_flag,exit_code", [
            ("create", True, True, 0),
            ("create", False, True, 1),
            ("create", True, False, 0),
            ("create", False, False, 1),
            ("delete", True, True, 0),
            ("delete", False, True, 1),
            ("delete", True, False, 0),
            ("delete", False, False, 1),
            ("update", True, True, 0),
            ("update", False, True, 1),
            ("update", True, False, 0),
            ("update", False, False, 1),
            ("launch", True, True, 0),
            ("launch", False, True, 1),
            ("launch", True, False, 0),
            ("launch", False, False, 1)
        ]
    )
    def test_stack_commands(self, command, success, yes_flag, exit_code):
        getattr(self.mock_stack, command).return_value = \
            StackStatus.COMPLETE if success else StackStatus.FAILED

        kwargs = {"args": [command, "dev/vpc.yaml"]}
        if yes_flag:
            kwargs["args"].append("-y")
        else:
            kwargs["input"] = "y\n"

        result = self.runner.invoke(cli, **kwargs)

        getattr(self.mock_stack, command).assert_called_with()
        assert result.exit_code == exit_code

    @pytest.mark.parametrize(
        "command,yes_flag", [
            ("create", True),
            ("create", False),
            ("delete", True),
            ("delete", False),
            ("execute", True),
            ("execute", False)
        ]
    )
    def test_change_set_commands(self, command, yes_flag):
        stack_command = command + "_change_set"

        kwargs = {"args": [command, "dev/vpc.yaml", "cs1"]}
        if yes_flag:
            kwargs["args"].append("-y")
        else:
            kwargs["input"] = "y\n"

        result = self.runner.invoke(cli, **kwargs)

        getattr(self.mock_stack, stack_command).assert_called_with("cs1")
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "command,success,yes_flag,exit_code", [
            ("delete", True, True, 0),
            ("delete", False, True, 1),
            ("delete", True, False, 0),
            ("delete", False, False, 1),
            ("launch", True, True, 0),
            ("launch", False, True, 1),
            ("launch", True, False, 0),
            ("launch", False, False, 1)
        ]
    )
    def test_stack_group_commands(self, command, success, yes_flag, exit_code):
        status = StackStatus.COMPLETE if success else StackStatus.FAILED
        response = {"stack": status}

        getattr(self.mock_stack_group, command).return_value = response

        kwargs = {"args": [command, "dev"]}
        if yes_flag:
            kwargs["args"].append("-y")
        else:
            kwargs["input"] = "y\n"

        result = self.runner.invoke(cli, **kwargs)

        getattr(self.mock_stack_group, command).assert_called_with()
        assert result.exit_code == exit_code

    @patch('sceptre.cli.update.uuid1')
    @patch('sceptre.cli.update.write')
    @pytest.mark.parametrize(
        "verbose_flag,yes_flag,cs_success", [
            (False, True, True),
            (False, False, True),
            (True, True, True),
            (True, False, True),
            (False, True, False),
            (False, False, False),
            (True, True, False),
            (True, False, False)
        ]
    )
    def test_update_with_change_set_with_input_yes(
        self, mock_write, mock_uuid1, verbose_flag, yes_flag, cs_success
    ):
        self.mock_stack.wait_for_cs_completion.return_value = \
            StackChangeSetStatus.READY if cs_success \
            else StackChangeSetStatus.DEFUNCT
        response = {
            "VerboseProperty": "VerboseProperty",
            "ChangeSetName": "ChangeSetName",
            "CreationTime": "CreationTime",
            "ExecutionStatus": "ExecutionStatus",
            "StackName": "StackName",
            "Status": "Status",
            "StatusReason": "StatusReason",
            "Changes": [
                {
                    "ResourceChange": {
                        "Action": "Action",
                        "LogicalResourceId": "LogicalResourceId",
                        "PhysicalResourceId": "PhysicalResourceId",
                        "Replacement": "Replacement",
                        "ResourceType": "ResourceType",
                        "Scope": "Scope",
                        "VerboseProperty": "VerboseProperty"
                    }
                }
            ]
        }
        self.mock_stack.describe_change_set.return_value = response

        mock_uuid1.return_value = UUID(int=0)

        kwargs = {"args": ["update", "dev/vpc.yaml", "-c"]}

        if verbose_flag:
            kwargs["args"].append("-v")

        if yes_flag:
            kwargs["args"].append("-y")
        else:
            kwargs["input"] = "y\n"

        result = self.runner.invoke(cli, **kwargs)

        if cs_success:
            if not verbose_flag:
                del response["VerboseProperty"]
                del response["Changes"][0]["ResourceChange"]["VerboseProperty"]
            mock_write.assert_called_once_with(response, 'yaml')
            self.mock_stack.execute_change_set.assert_called_once_with(
                "change-set-00000000000000000000000000000000"
            )

        self.mock_stack.delete_change_set.assert_called_once_with(
            "change-set-00000000000000000000000000000000"
        )

        assert result.exit_code == (0 if cs_success else 1)

    @pytest.mark.parametrize(
        "verbose_flag,", [
            (False),
            (True)
        ]
    )
    def test_describe_change_set(self, verbose_flag):
        response = {
            "VerboseProperty": "VerboseProperty",
            "ChangeSetName": "ChangeSetName",
            "CreationTime": "CreationTime",
            "ExecutionStatus": "ExecutionStatus",
            "StackName": "StackName",
            "Status": "Status",
            "StatusReason": "StatusReason",
            "Changes": [
                {
                    "ResourceChange": {
                        "Action": "Action",
                        "LogicalResourceId": "LogicalResourceId",
                        "PhysicalResourceId": "PhysicalResourceId",
                        "Replacement": "Replacement",
                        "ResourceType": "ResourceType",
                        "Scope": "Scope",
                        "VerboseProperty": "VerboseProperty"
                    }
                }
            ]
        }
        args = ["describe", "change-set", "dev/vpc.yaml", "cs1"]
        if verbose_flag:
            args.append("-v")

        self.mock_stack.describe_change_set.return_value = response
        result = self.runner.invoke(cli, args)
        if not verbose_flag:
            del response["VerboseProperty"]
            del response["Changes"][0]["ResourceChange"]["VerboseProperty"]
        assert yaml.load(result.output) == response
        assert result.exit_code == 0

    def test_list_change_sets_with_200(self):
        self.mock_stack.list_change_sets.return_value = {
            "ResponseMetadata": {
                "HTTPStatusCode": 200
            },
            "ChangeSets": "Test"
        }
        result = self.runner.invoke(
            cli, ["list", "change-sets", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert yaml.load(result.output) == {"ChangeSets": "Test"}

    def test_list_change_sets_without_200(self):
        response = {
            "ResponseMetadata": {
                "HTTPStatusCode": 404
            },
            "ChangeSets": "Test"
        }
        self.mock_stack.list_change_sets.return_value = response

        result = self.runner.invoke(
            cli, ["list", "change-sets", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert yaml.load(result.output) == response

    def test_list_outputs(self):
        outputs = [{"OutputKey": "Key", "OutputValue": "Value"}]
        self.mock_stack.describe_outputs.return_value = outputs
        result = self.runner.invoke(
            cli, ["list", "outputs", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert yaml.load(result.output) == outputs

    def test_list_outputs_with_export(self):
        outputs = [{"OutputKey": "Key", "OutputValue": "Value"}]
        self.mock_stack.describe_outputs.return_value = outputs
        result = self.runner.invoke(
            cli, ["list", "outputs", "dev/vpc.yaml", "-e", "envvar"]
        )
        assert result.exit_code == 0
        assert yaml.load(result.output) == "export SCEPTRE_Key=Value"

    def test_status_with_group(self):
        self.mock_stack_group.describe.return_value = {"stack": "status"}

        result = self.runner.invoke(cli, ["status", "dev"])
        assert result.exit_code == 0
        assert result.output == "stack: status\n\n"

    def test_status_with_stack(self):
        self.mock_stack.get_status.return_value = "status"

        result = self.runner.invoke(cli, ["status", "dev/vpc.yaml"])
        assert result.exit_code == 0
        assert result.output == "status\n"

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

    def test_init_project_another_exception(self):
        self.patcher_getcwd.stop()
        with self.runner.isolated_filesystem():
            patcher_mkdir = patch("sceptre.cli.init.os.mkdir")
            mock_mkdir = patcher_mkdir.start()
            mock_mkdir.side_effect = OSError(errno.EINVAL)
            result = self.runner.invoke(cli, ["init", "project", "example"])
            mock_mkdir = patcher_mkdir.stop()
            assert str(result.exception) == str(OSError(errno.EINVAL))
        self.patcher_getcwd.start()

    @pytest.mark.parametrize(
      "stack_group,config_structure,stdin,result", [
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
      ]
    )
    def test_init_stack_group(
        self, stack_group, config_structure, stdin, result
    ):
        self.patcher_getcwd.stop()
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
            os.makedirs(config_dir)

            stack_group_dir = os.path.join(sceptre_dir, "config", stack_group)
            for stack_group_path, config in config_structure.items():
                path = os.path.join(config_dir, stack_group_path)
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
                cli, ["init", "grp", stack_group],
                input=stdin
            )

            if result:
                with open(os.path.join(stack_group_dir, "config.yaml"))\
                  as config_file:
                    config = yaml.load(config_file)
                assert config == result
            else:
                assert cmd_result.output.endswith(
                    "No config.yaml file needed - covered by parent config.\n"
                )
        self.patcher_getcwd.start()

    def test_init_stack_group_with_existing_folder(self):
        self.patcher_getcwd.stop()
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
            stack_group_dir = os.path.join(config_dir, "A")

            os.makedirs(stack_group_dir)
            os.chdir(sceptre_dir)

            cmd_result = self.runner.invoke(
                cli, ["init", "grp", "A"], input="y\n\n\n"
            )

            assert cmd_result.output.startswith(
                "StackGroup path exists. "
                "Do you want initialise config.yaml?"
            )
            with open(os.path.join(
                  stack_group_dir, "config.yaml")) as config_file:
                config = yaml.load(config_file)
            assert config == {"project_code": "", "region": ""}

        self.patcher_getcwd.start()

    def test_init_stack_group_with_another_exception(self):
        self.patcher_getcwd.stop()
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
            stack_group_dir = os.path.join(config_dir, "A")

            os.makedirs(stack_group_dir)
            os.chdir(sceptre_dir)

            patcher_mkdir = patch("sceptre.cli.init.os.mkdir")
            mock_mkdir = patcher_mkdir.start()
            mock_mkdir.side_effect = OSError(errno.EINVAL)
            result = self.runner.invoke(cli, ["init", "grp", "A"])
            mock_mkdir = patcher_mkdir.stop()
            assert str(result.exception) == str(OSError(errno.EINVAL))

        self.patcher_getcwd.start()

    def test_setup_logging_with_debug(self):
        logger = setup_logging(True, False)
        assert logger.getEffectiveLevel() == logging.DEBUG
        assert logging.getLogger("botocore").getEffectiveLevel() == \
            logging.INFO

        # Silence logging for the rest of the tests
        logger.setLevel(logging.CRITICAL)

    def test_setup_logging_without_debug(self):
        logger = setup_logging(False, False)
        assert logger.getEffectiveLevel() == logging.INFO
        assert logging.getLogger("botocore").getEffectiveLevel() == \
            logging.CRITICAL

        # Silence logging for the rest of the tests
        logger.setLevel(logging.CRITICAL)

    @patch("sceptre.cli.click.echo")
    def test_write_with_yaml_format(self, mock_echo):
        write({"key": "value"}, "yaml")
        mock_echo.assert_called_once_with("key: value\n")

    @patch("sceptre.cli.click.echo")
    def test_write_with_json_format(self, mock_echo):
        write({"key": "value"}, "json")
        mock_echo.assert_called_once_with('{"key": "value"}')

    @patch("sceptre.cli.click.echo")
    def test_write_status_with_colour(self, mock_echo):
        write("stack: CREATE_COMPLETE", no_colour=False)
        mock_echo.assert_called_once_with(
            "stack: \x1b[32mCREATE_COMPLETE\x1b[0m"
        )

    @patch("sceptre.cli.click.echo")
    def test_write_status_without_colour(self, mock_echo):
        write("stack: CREATE_COMPLETE", no_colour=True)
        mock_echo.assert_called_once_with("stack: CREATE_COMPLETE")

    @patch("sceptre.cli.helpers.StackStatusColourer.colour")
    @patch("sceptre.cli.helpers.logging.Formatter.format")
    def test_ColouredFormatter_format_with_string(
            self, mock_format, mock_colour
    ):
        mock_format.return_value = sentinel.response
        mock_colour.return_value = sentinel.coloured_response
        coloured_formatter = ColouredFormatter()
        response = coloured_formatter.format("string")
        mock_format.assert_called_once_with("string")
        mock_colour.assert_called_once_with(sentinel.response)
        assert response == sentinel.coloured_response

    def test_CustomJsonEncoder_with_non_json_serialisable_object(self):
        encoder = CustomJsonEncoder()
        response = encoder.encode(datetime.datetime(2016, 5, 3))
        assert response == '"2016-05-03 00:00:00"'

    def test_get_stack_or_stack_group_with_stack(self):
        ctx = MagicMock(obj={
            "sceptre_dir": sentinel.sceptre_dir,
            "user_variables": sentinel.user_variables
        })
        stack, stack_group = get_stack_or_stack_group(ctx, "stack.yaml")
        self.mock_ConfigReader.assert_called_once_with(
            sentinel.sceptre_dir, sentinel.user_variables
        )
        assert isinstance(stack, Stack)
        assert stack_group is None

    def test_get_stack_or_stack_group_with_nested_stack(self):
        ctx = MagicMock(obj={
            "sceptre_dir": sentinel.sceptre_dir,
            "user_variables": sentinel.user_variables
        })
        stack, stack_group = get_stack_or_stack_group(
                ctx, "stack-group/dir/stack.yaml"
        )
        self.mock_ConfigReader.assert_called_once_with(
            sentinel.sceptre_dir, sentinel.user_variables
        )
        assert isinstance(stack, Stack)
        assert stack_group is None

    def test_get_stack_or_stack_group_with_group(self):
        ctx = MagicMock(obj={
            "sceptre_dir": sentinel.sceptre_dir,
            "user_variables": sentinel.user_variables
        })
        stack, stack_group = get_stack_or_stack_group(ctx, "stack-group/dir")
        self.mock_ConfigReader.assert_called_once_with(
            sentinel.sceptre_dir, sentinel.user_variables
        )
        assert isinstance(stack_group, StackGroup)
        assert stack is None
