import logging
import yaml
import datetime
import os
import errno

from click.testing import CliRunner
from mock import MagicMock, patch, sentinel
import pytest
import click

from sceptre.cli import cli
from sceptre.config.reader import ConfigReader
from sceptre.stack import Stack
from sceptre.plan.actions import StackActions
from sceptre.stack_status import StackStatus
from sceptre.cli.helpers import setup_logging, write, ColouredFormatter
from sceptre.cli.helpers import CustomJsonEncoder, catch_exceptions
from botocore.exceptions import ClientError
from sceptre.exceptions import SceptreException


class TestCli(object):

    def setup_method(self, test_method):
        self.patcher_ConfigReader = patch("sceptre.plan.plan.ConfigReader")
        self.patcher_StackActions = patch("sceptre.plan.executor.StackActions")

        self.mock_ConfigReader = self.patcher_ConfigReader.start()
        self.mock_StackActions = self.patcher_StackActions.start()

        self.mock_config_reader = MagicMock(spec=ConfigReader)
        self.mock_stack_actions = MagicMock(spec=StackActions)

        self.mock_stack = MagicMock(spec=Stack)

        self.mock_stack.name = 'mock-stack'
        self.mock_stack.region = None
        self.mock_stack.profile = None
        self.mock_stack.external_name = None
        self.mock_stack.dependencies = []

        self.mock_config_reader.construct_stacks.return_value = \
            set([self.mock_stack]), set([self.mock_stack])

        self.mock_stack_actions.stack = self.mock_stack

        self.mock_ConfigReader.return_value = self.mock_config_reader
        self.mock_StackActions.return_value = self.mock_stack_actions

        self.runner = CliRunner()

    def teardown_method(self, test_method):
        self.patcher_ConfigReader.stop()
        self.patcher_StackActions.stop()

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
            click.echo(yaml.safe_dump(ctx.obj.get("user_variables")))

        with self.runner.isolated_filesystem():
            for name, content in files.items():
                with open(name, "w") as fh:
                    yaml.safe_dump(content, fh)

            result = self.runner.invoke(cli, command)

        user_variables = yaml.safe_load(result.output)
        assert result.exit_code == 0
        assert user_variables == output

    def test_validate_template_with_valid_template(self):
        self.mock_stack_actions.validate.return_value = {
            "Parameters": "Example",
            "ResponseMetadata": {
                "HTTPStatusCode": 200
            }
        }
        result = self.runner.invoke(cli, ["validate", "dev/vpc.yaml"])
        self.mock_stack_actions.validate.assert_called_with()

        assert result.output == "Template mock-stack is valid. Template details:\n\n" \
            "{'Parameters': 'Example'}\n"

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
        self.mock_stack_actions.validate.side_effect = client_error

        expected_result = str(client_error) + "\n"
        result = self.runner.invoke(cli, ["validate", "dev/vpc.yaml"])
        assert expected_result in result.output

    def test_estimate_template_cost_with_browser(self):
        self.mock_stack_actions.estimate_cost.return_value = {
            "Url": "http://example.com",
            "ResponseMetadata": {
                "HTTPStatusCode": 200
            }
        }

        args = ["estimate-cost", "dev/vpc.yaml"]
        result = self.runner.invoke(cli, args)

        self.mock_stack_actions.estimate_cost.assert_called_with()

        assert result.output == \
            '{0}{1}'.format("View the estimated cost for mock-stack at:\n",
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
        self.mock_stack_actions.estimate_cost.side_effect = client_error

        expected_result = str(client_error) + "\n"
        result = self.runner.invoke(
            cli,
            ["estimate-cost", "dev/vpc.yaml"]
        )
        assert expected_result in result.output

    def test_lock_stack(self):
        self.runner.invoke(
            cli, ["set-policy", "dev/vpc.yaml", "-b", "deny-all"]
        )
        self.mock_config_reader.construct_stacks.assert_called_with()
        self.mock_stack_actions.lock.assert_called_with()

    def test_unlock_stack(self):
        self.runner.invoke(
            cli, ["set-policy", "dev/vpc.yaml", "-b", "allow-all"]
        )
        self.mock_config_reader.construct_stacks.assert_called_with()
        self.mock_stack_actions.unlock.assert_called_with()

    def test_set_policy_with_file_flag(self):
        policy_file = "tests/fixtures/stack_policies/lock.json"
        result = self.runner.invoke(cli, [
            "set-policy", "dev/vpc.yaml", policy_file
        ])
        assert result.exit_code == 0

    def test_describe_policy_with_existing_policy(self):
        self.mock_stack_actions.get_policy.return_value = {
            "dev/vpc": {"Statement": ["Body"]}
        }

        result = self.runner.invoke(
            cli, ["describe", "policy", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert result.output == "{'dev/vpc': {'Statement': ['Body']}}\n"

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
        self.mock_stack_actions.describe_resources.return_value = response
        result = self.runner.invoke(cli, ["list", "resources", "dev"])

        assert yaml.safe_load(result.output) == [response]
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
        self.mock_stack_actions.describe_resources.return_value = response
        result = self.runner.invoke(cli, ["list", "resources", "dev/vpc.yaml"])
        assert yaml.safe_load(result.output) == [response]
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
        run_command = getattr(self.mock_stack_actions, command)
        run_command.return_value = \
            StackStatus.COMPLETE if success else StackStatus.FAILED

        kwargs = {"args": [command, "dev/vpc.yaml"]}
        if yes_flag:
            kwargs["args"].append("-y")
        else:
            kwargs["input"] = "y\n"

        result = self.runner.invoke(cli, **kwargs)

        run_command.assert_called_with()
        assert result.exit_code == exit_code

    @pytest.mark.parametrize(
        "command, ignore_dependencies", [
            ("create", True),
            ("create", False),
            ("delete", True),
            ("delete", False),
        ]
    )
    def test_ignore_dependencies_commands(self, command, ignore_dependencies):
        args = [command, "dev/vpc.yaml", "cs-1", "-y"]
        if ignore_dependencies:
            args.insert(0, "--ignore-dependencies")
        result = self.runner.invoke(cli, args)
        assert result.exit_code == 0

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

        getattr(self.mock_stack_actions,
                stack_command).assert_called_with("cs1")
        assert result.exit_code == 0

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
        args = ["describe", "change-set", "region/vpc.yaml", "cs1"]
        if verbose_flag:
            args.append("-v")

        self.mock_stack_actions.describe_change_set.return_value = response
        result = self.runner.invoke(cli, args)
        if not verbose_flag:
            del response["VerboseProperty"]
            del response["Changes"][0]["ResourceChange"]["VerboseProperty"]
        assert yaml.safe_load(result.output) == response
        assert result.exit_code == 0

    def test_list_change_sets_with_200(self):
        self.mock_stack_actions.list_change_sets.return_value = {
            "ChangeSets": "Test"
        }
        result = self.runner.invoke(
            cli, ["list", "change-sets", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert yaml.safe_load(result.output) == {"ChangeSets": "Test"}

    def test_list_change_sets_without_200(self):
        response = {
            "ChangeSets": "Test"
        }
        self.mock_stack_actions.list_change_sets.return_value = response

        result = self.runner.invoke(
            cli, ["list", "change-sets", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert yaml.safe_load(result.output) == response

    def test_list_outputs(self):
        outputs = [{"OutputKey": "Key", "OutputValue": "Value"}]
        self.mock_stack_actions.describe_outputs.return_value = outputs
        result = self.runner.invoke(
            cli, ["list", "outputs", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert yaml.safe_load(result.output) == [outputs]

    def test_list_outputs_with_export(self):
        outputs = {'stack': [{"OutputKey": "Key", "OutputValue": "Value"}]}
        self.mock_stack_actions.describe_outputs.return_value = outputs
        result = self.runner.invoke(
            cli, ["list", "outputs", "dev/vpc.yaml", "-e", "envvar"]
        )
        assert result.exit_code == 0
        assert yaml.safe_load(result.output) == "export SCEPTRE_Key='Value'"

    def test_status_with_group(self):
        self.mock_stack_actions.get_status.return_value = {
            "stack": "status"
        }

        result = self.runner.invoke(cli, ["status", "dev"])
        assert result.exit_code == 0
        assert result.output == "mock-stack: {'stack': 'status'}\n"

    def test_status_with_stack(self):
        self.mock_stack_actions.get_status.return_value = "status"
        result = self.runner.invoke(cli, ["status", "dev/vpc.yaml"])
        assert result.exit_code == 0
        assert result.output == "mock-stack: status\n"

    def test_new_project_non_existant(self):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
            config_dir = os.path.join(project_path, "config")
            template_dir = os.path.join(project_path, "templates")
            region = "test-region"
            os.environ["AWS_DEFAULT_REGION"] = region
            defaults = {
                "project_code": "example",
                "region": region
            }

            result = self.runner.invoke(cli, ["new", "project", "example"])
            assert not result.exception
            assert os.path.isdir(config_dir)
            assert os.path.isdir(template_dir)

            with open(os.path.join(config_dir, "config.yaml")) as config_file:
                config = yaml.safe_load(config_file)

            assert config == defaults

    def test_new_project_already_exist(self):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
            config_dir = os.path.join(project_path, "config")
            template_dir = os.path.join(project_path, "templates")
            existing_config = {"Test": "Test"}

            os.mkdir(project_path)
            os.mkdir(config_dir)
            os.mkdir(template_dir)

            config_filepath = os.path.join(config_dir, "config.yaml")
            with open(config_filepath, 'w') as config_file:
                yaml.dump(existing_config, config_file)

            result = self.runner.invoke(cli, ["new", "project", "example"])
            assert result.exit_code == 1
            assert result.output == 'Folder \"example\" already exists.\n'
            assert os.path.isdir(config_dir)
            assert os.path.isdir(template_dir)

            with open(os.path.join(config_dir, "config.yaml")) as config_file:
                config = yaml.safe_load(config_file)
            assert existing_config == config

    def test_new_project_another_exception(self):
        with self.runner.isolated_filesystem():
            patcher_mkdir = patch("sceptre.cli.new.os.mkdir")
            mock_mkdir = patcher_mkdir.start()
            mock_mkdir.side_effect = OSError(errno.EINVAL)
            result = self.runner.invoke(cli, ["new", "project", "example"])
            mock_mkdir = patcher_mkdir.stop()
            assert str(result.exception) == str(OSError(errno.EINVAL))

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
    def test_create_new_stack_group_folder(
        self, stack_group, config_structure, stdin, result
    ):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
            config_dir = os.path.join(project_path, "config")
            os.makedirs(config_dir)

            stack_group_dir = os.path.join(project_path, "config", stack_group)
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

            os.chdir(project_path)

            cmd_result = self.runner.invoke(
                cli, ["new", "group", stack_group],
                input=stdin
            )

            if result:
                with open(os.path.join(stack_group_dir, "config.yaml"))\
                        as config_file:
                    config = yaml.safe_load(config_file)
                assert config == result
            else:
                assert cmd_result.output.endswith(
                    "No config.yaml file needed - covered by parent config.\n"
                )

    def test_new_stack_group_folder_with_existing_folder(self):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
            config_dir = os.path.join(project_path, "config")
            stack_group_dir = os.path.join(config_dir, "A")

            os.makedirs(stack_group_dir)
            os.chdir(project_path)

            cmd_result = self.runner.invoke(
                cli, ["new", "group", "A"], input="y\n\n\n"
            )

            assert cmd_result.output.startswith(
                "StackGroup path exists. "
                "Do you want initialise config.yaml?"
            )
            with open(os.path.join(
                    stack_group_dir, "config.yaml")) as config_file:
                config = yaml.safe_load(config_file)
            assert config == {"project_code": "", "region": ""}

    def test_new_stack_group_folder_with_another_exception(self):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
            config_dir = os.path.join(project_path, "config")
            stack_group_dir = os.path.join(config_dir, "A")

            os.makedirs(stack_group_dir)
            os.chdir(project_path)
            patcher_mkdir = patch("sceptre.cli.new.os.mkdir")
            mock_mkdir = patcher_mkdir.start()
            mock_mkdir.side_effect = OSError(errno.EINVAL)
            result = self.runner.invoke(cli, ["new", "group", "A"])
            mock_mkdir = patcher_mkdir.stop()
            assert str(result.exception) == str(OSError(errno.EINVAL))

    @pytest.mark.parametrize(
        "cli_module,command,output_format,no_colour", [
            (
                'describe',
                ['describe', 'change-set', 'somepath', 'cs1'],
                'yaml',
                True
            ),
            (
                'describe',
                ['describe', 'change-set', 'somepath', 'cs1'],
                'json',
                False
            ),
            (
                'describe',
                ['describe', 'policy', 'somepolicy'],
                'yaml',
                True
            ),
            (
                'describe',
                ['describe', 'policy', 'somepolicy'],
                'json',
                False
            )
        ]
    )
    def test_write_output_format_flags(
        self, cli_module, command, output_format, no_colour
    ):
        no_colour_flag = ['--no-colour'] if no_colour else []
        output_format_flag = ['--output', output_format]
        args = output_format_flag + no_colour_flag + command

        with patch("sceptre.cli." + cli_module + ".write") as mock_write:
            self.runner.invoke(cli, args)
            mock_write.assert_called()
            for call in mock_write.call_args_list:
                args, _ = call
                assert args[1] == output_format
                assert args[2] == no_colour

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
    @pytest.mark.parametrize(
        "output_format,no_colour,expected_output", [
            ("json", True, '{\n    "stack": "CREATE_COMPLETE"\n}'),
            ("json", False, '{\n    "stack": "\x1b[32mCREATE_COMPLETE\x1b[0m\"\n}'),
            ("yaml", True, {'stack': 'CREATE_COMPLETE'}),
            ("yaml", False, '{\'stack\': \'\x1b[32mCREATE_COMPLETE\x1b[0m\'}')
        ]
    )
    def test_write_formats(
        self, mock_echo, output_format, no_colour, expected_output
    ):
        write({"stack": "CREATE_COMPLETE"}, output_format, no_colour)
        mock_echo.assert_called_once_with(expected_output)

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
