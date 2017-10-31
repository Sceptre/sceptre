import logging
import yaml
import datetime
import os
import errno
from uuid import UUID

from click.testing import CliRunner
from mock import patch, sentinel, MagicMock
import pytest

import sceptre.cli
from sceptre.cli import cli
from sceptre.environment import Environment
from sceptre.exceptions import SceptreException, RecursiveFlagMissingError
from sceptre.exceptions import StackConfigNotFoundError
from sceptre.stack import Stack
from sceptre.stack_status import StackStatus
from sceptre.stack_status import StackChangeSetStatus
from sceptre.template import Template


class TestCli(object):

    def setup_method(self, test_method):
        self.runner = CliRunner()

    @patch("sys.exit")
    def test_catch_excecptions(self, mock_exit):
            @sceptre.cli.helpers.catch_exceptions
            def raises_exception():
                raise SceptreException

            raises_exception()
            mock_exit.assert_called_once_with(1)

    @patch("sceptre.cli.template.write")
    @patch("sceptre.cli.template.get_stack")
    def test_validate_template(self, mock_get_stack, mock_write):
        stack = MagicMock(spec=Stack)
        stack.template = MagicMock(spec=Template)
        mock_get_stack.return_value = stack
        self.runner.invoke(cli, ["validate", "dev/vpc.yaml"])
        mock_write.assert_called_with(stack.template.validate(), 'yaml')

    @patch("sceptre.cli.template.get_stack")
    def test_generate_template(self, mock_get_stack):
        stack = MagicMock(spec=Stack)
        stack.template = MagicMock(spec=Template)
        stack.template.body = "template_body"
        mock_get_stack.return_value = stack
        result = self.runner.invoke(cli, ["generate", "dev/vpc.yaml"])

        assert result.output == "template_body\n"

    @patch("sceptre.cli.policy.get_stack")
    def test_lock_stack(self, mock_get_stack):
        stack = MagicMock(spec=Stack)
        mock_get_stack.return_value = stack
        self.runner.invoke(
            cli, ["set-policy", "dev/vpc.yaml", "-b", "deny-all"]
        )
        stack.lock.assert_called_once_with()

    @patch("sceptre.cli.policy.get_stack")
    def test_unlock_stack(self, mock_get_stack):
        stack = MagicMock(spec=Stack)
        mock_get_stack.return_value = stack
        self.runner.invoke(
            cli, ["set-policy", "dev/vpc.yaml", "-b", "allow-all"]
        )
        stack.unlock.assert_called_once_with()

    @patch("sceptre.cli.policy.get_stack")
    def test_set_policy_with_file_flag(self, mock_get_stack):
        stack = MagicMock(spec=Stack)
        mock_get_stack.return_value = stack
        policy_file = "tests/fixtures/stack_policies/lock.json"
        result = self.runner.invoke(cli, [
            "set-policy", "dev/vpc.yaml", policy_file
        ])
        assert result.exit_code == 0
        stack.set_policy.assert_called_once_with(policy_file)

    @patch("sceptre.cli.describe.get_stack")
    def test_describe_policy_with_existing_policy(self, mock_get_stack):
        stack = MagicMock(spec=Stack)
        stack.get_policy.return_value = {
            "StackPolicyBody": "Body"
        }
        mock_get_stack.return_value = stack

        result = self.runner.invoke(
            cli, ["describe", "policy", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert result.output == "Body\n"

    @patch("sceptre.cli.describe.get_stack")
    def test_describe_policy_without_existing_policy(self, mock_get_stack):
        stack = MagicMock(spec=Stack)
        stack.get_policy.return_value = {}
        mock_get_stack.return_value = stack

        result = self.runner.invoke(
            cli, ["describe", "policy", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        assert result.output == "{}\n"

    @patch("sceptre.cli.create.get_stack")
    def test_create_stack(self, mock_get_stack):
        stack = MagicMock(spec=Stack)
        stack.create.return_value = StackStatus.COMPLETE
        mock_get_stack.return_value = stack

        result = self.runner.invoke(cli, ["create", "dev/vpc.yaml"])
        stack.create.assert_called_with()
        assert result.exit_code == 0

    @patch("sceptre.cli.create.get_stack")
    def test_create_change_set(self, mock_get_stack):
        stack = MagicMock(spec=Stack)
        mock_get_stack.return_value = stack
        result = self.runner.invoke(cli, ["create", "dev/vpc.yaml", "cs1"])
        stack.create_change_set.assert_called_with("cs1")
        assert result.exit_code == 0

    @patch("sceptre.cli.delete.get_stack_and_env")
    def test_delete_stack(self, mock_get_stack_and_env):
        stack = MagicMock(spec=Stack)
        stack.delete.return_value = StackStatus.COMPLETE
        env = MagicMock(spec=Environment)
        mock_get_stack_and_env.return_value = (stack, env)

        result = self.runner.invoke(cli, ["delete", "dev/vpc.yaml"])
        stack.delete.assert_called_once_with()
        assert result.exit_code == 0

    @patch("sceptre.cli.delete.get_stack_and_env")
    def test_delete_env(self, mock_get_stack_and_env):
        env = MagicMock(spec=Environment)
        env.delete.return_value = {"stack": StackStatus.COMPLETE}
        mock_get_stack_and_env.return_value = (None, env)

        result = self.runner.invoke(cli, ["delete", "dev"])
        env.delete.assert_called_once_with()
        assert result.exit_code == 0

    @patch("sceptre.cli.delete.get_stack_and_env")
    def test_delete_env_fails(self, mock_get_stack_and_env):
        env = MagicMock(spec=Environment)
        env.delete.return_value = {"stack": StackStatus.FAILED}
        mock_get_stack_and_env.return_value = (None, env)

        result = self.runner.invoke(cli, ["delete", "dev"])
        env.delete.assert_called_once_with()
        assert result.exit_code == 1

    @patch("sceptre.cli.delete.get_stack_and_env")
    def test_delete_change_set(self, mock_get_stack_and_env):
        stack = MagicMock(spec=Stack)
        env = MagicMock(spec=Environment)
        mock_get_stack_and_env.return_value = (stack, env)

        result = self.runner.invoke(cli, ["delete", "dev/vpc.yaml", "cs1"])
        stack.delete_change_set.assert_called_once_with("cs1")
        assert result.exit_code == 0

    @patch("sceptre.cli.update.get_stack")
    def test_update_stack(self, mock_get_stack):
        stack = MagicMock(spec=Stack)
        stack.update.return_value = StackStatus.COMPLETE
        mock_get_stack.return_value = stack

        result = self.runner.invoke(cli, ["update", "dev/vpc.yaml"])
        stack.update.assert_called_once_with()
        assert result.exit_code == 0

    @patch('sceptre.cli.update.uuid1')
    @patch('sceptre.cli.update.write')
    @patch("sceptre.cli.update.get_stack")
    @patch("sceptre.cli.update.simplify_change_set_description")
    def test_update_with_change_set_with_input_yes(
        self, mock_simplify_change_set_description, mock_get_stack,
        mock_write, mock_uuid1
    ):
        mock_simplify_change_set_description.return_value = "not_verbose"
        stack = MagicMock(spec=Stack)
        stack.wait_for_cs_completion.return_value = StackChangeSetStatus.READY
        stack.describe_change_set.return_value = "verbose"
        mock_get_stack.return_value = stack
        mock_uuid1.return_value = UUID(int=0)

        result = self.runner.invoke(
            cli, ["update", "dev/vpc.yaml", "-c"], input="y"
        )
        assert result.exit_code == 0
        mock_write.assert_called_once_with("not_verbose", 'yaml')
        stack.execute_change_set.assert_called_once_with(
            "change-set-00000000000000000000000000000000"
        )

    @patch('sceptre.cli.update.uuid1')
    @patch('sceptre.cli.update.write')
    @patch("sceptre.cli.update.get_stack")
    @patch("sceptre.cli.update.simplify_change_set_description")
    def test_update_with_change_set_without_verbose_flag(
        self, mock_simplify_change_set_description, mock_get_stack,
        mock_write, mock_uuid1
    ):
        mock_simplify_change_set_description.return_value = "not_verbose"
        stack = MagicMock(spec=Stack)
        stack.wait_for_cs_completion.return_value = StackChangeSetStatus.READY
        stack.describe_change_set.return_value = "verbose"
        mock_get_stack.return_value = stack
        mock_uuid1.return_value = UUID(int=0)

        result = self.runner.invoke(
            cli, ["update", "dev/vpc.yaml", "-c", "-v"], input="y"
        )
        assert result.exit_code == 0
        mock_write.assert_called_once_with("verbose", 'yaml')
        stack.execute_change_set.assert_called_once_with(
            "change-set-00000000000000000000000000000000"
        )

    @patch('sceptre.cli.update.uuid1')
    @patch('sceptre.cli.update.write')
    @patch("sceptre.cli.update.get_stack")
    @patch("sceptre.cli.update.simplify_change_set_description")
    def test_update_with_change_set_with_input_no(
        self, mock_simplify_change_set_description, mock_get_stack,
        mock_write, mock_uuid1
    ):
        mock_simplify_change_set_description.return_value = "not_verbose"
        stack = MagicMock(spec=Stack)
        stack.wait_for_cs_completion.return_value = StackChangeSetStatus.READY
        stack.describe_change_set.return_value = "verbose"
        mock_get_stack.return_value = stack
        mock_uuid1.return_value = UUID(int=0)

        result = self.runner.invoke(
            cli, ["update", "dev/vpc.yaml", "-c"], input="n"
        )
        assert result.exit_code == 0
        mock_write.assert_called_once_with("not_verbose", 'yaml')
        stack.execute_change_set.assert_not_called()
        stack.delete_change_set.assert_called_once_with(
            "change-set-00000000000000000000000000000000"
        )

    @patch('sceptre.cli.update.uuid1')
    @patch('sceptre.cli.update.write')
    @patch("sceptre.cli.update.get_stack")
    @patch("sceptre.cli.update.simplify_change_set_description")
    def test_update_with_change_set_with_status_defunct(
        self, mock_simplify_change_set_description, mock_get_stack,
        mock_write, mock_uuid1
    ):
        mock_simplify_change_set_description.return_value = "not_verbose"
        stack = MagicMock(spec=Stack)
        stack.wait_for_cs_completion.return_value = \
            StackChangeSetStatus.DEFUNCT
        stack.describe_change_set.return_value = "verbose"
        mock_get_stack.return_value = stack
        mock_uuid1.return_value = UUID(int=0)

        result = self.runner.invoke(
            cli, ["update", "dev/vpc.yaml", "-c"], input="y"
        )
        assert result.exit_code == 1
        mock_write.assert_called_once_with("not_verbose", 'yaml')
        stack.execute_change_set.assert_not_called()
        stack.delete_change_set.assert_called_once_with(
            "change-set-00000000000000000000000000000000"
        )

    @patch("sceptre.cli.launch.get_stack_and_env")
    def test_launch_stack(self, mock_get_stack_and_env):
        stack = MagicMock(spec=Stack)
        stack.launch.return_value = StackStatus.COMPLETE
        env = MagicMock(spec=Environment)
        mock_get_stack_and_env.return_value = (stack, env)
        result = self.runner.invoke(cli, ["launch", "dev/vpc.yaml"])
        stack.launch.assert_called_once_with()
        assert result.exit_code == 0

    @patch("sceptre.cli.launch.get_stack_and_env")
    def test_launch_stack_with_failure(self, mock_get_stack_and_env):
        stack = MagicMock(spec=Stack)
        stack.launch.return_value = StackStatus.FAILED
        env = MagicMock(spec=Environment)
        mock_get_stack_and_env.return_value = (stack, env)
        result = self.runner.invoke(cli, ["launch", "dev/vpc.yaml"])
        stack.launch.assert_called_once_with()
        assert result.exit_code == 1

    @patch("sceptre.cli.launch.get_stack_and_env")
    def test_launch_env(self, mock_get_stack_and_env):
        env = MagicMock(spec=Environment)
        env.launch.return_value = {"stack": StackStatus.COMPLETE}
        mock_get_stack_and_env.return_value = (None, env)
        result = self.runner.invoke(cli, ["launch", "dev", "-r"])
        env.launch.assert_called_once_with()
        assert result.exit_code == 0

    @patch("sceptre.cli.launch.get_stack_and_env")
    def test_launch_env_with_failure(self, mock_get_stack_and_env):
        env = MagicMock(spec=Environment)
        env.launch.return_value = {"stack": StackStatus.FAILED}
        mock_get_stack_and_env.return_value = (None, env)
        result = self.runner.invoke(cli, ["launch", "dev", "-r"])
        env.launch.assert_called_once_with()
        assert result.exit_code == 1

    @patch("sceptre.cli.execute.get_stack")
    def test_execute_change_set(self, mock_get_stack):
        stack = MagicMock(spec=Stack)
        mock_get_stack.return_value = stack

        self.runner.invoke(cli, ["execute", "dev/vpc.yaml", "cs1"])
        stack.execute_change_set.assert_called_once_with("cs1")

    @patch('sceptre.cli.describe.write')
    @patch("sceptre.cli.describe.get_stack_and_env")
    def test_list_stack_resources(self, mock_get_stack_and_env, mock_write):
        stack = MagicMock(spec=Stack)
        stack.delete.return_value = StackStatus.COMPLETE
        env = MagicMock(spec=Environment)
        mock_get_stack_and_env.return_value = (stack, env)

        self.runner.invoke(cli, ["list", "resources", "dev/vpc.yaml"])
        mock_write.assert_called_once_with(stack.describe_resources(), 'yaml')

    @patch('sceptre.cli.describe.write')
    @patch("sceptre.cli.describe.get_stack_and_env")
    def test_list_env_resources(self, mock_get_stack_and_env, mock_write):
        stack = MagicMock(spec=Stack)
        stack.delete.return_value = StackStatus.COMPLETE
        env = MagicMock(spec=Environment)
        mock_get_stack_and_env.return_value = (None, env)

        self.runner.invoke(cli, ["list", "resources", "dev", "-r"])
        mock_write.assert_called_once_with(env.describe_resources(), 'yaml')

    @patch('sceptre.cli.describe.write')
    @patch("sceptre.cli.describe.get_stack")
    @patch("sceptre.cli.describe._simplify_change_set_description")
    def test_describe_change_set(
        self, mock_simplify_change_set_description, mock_get_stack, mock_write
    ):
        stack = MagicMock(spec=Stack)
        stack.launch.return_value = StackStatus.COMPLETE
        mock_get_stack.return_value = stack
        stack.describe_change_set.return_value = "verbose"
        mock_simplify_change_set_description.return_value = "not_verbose"
        self.runner.invoke(
            cli, ["describe", "change-set", "dev/vpc.yaml", "cs1"]
        )
        stack.describe_change_set.assert_called_once_with("cs1")
        mock_write.assert_called_once_with("not_verbose", 'yaml')

    @patch('sceptre.cli.describe.write')
    @patch("sceptre.cli.describe.get_stack")
    @patch("sceptre.cli.describe._simplify_change_set_description")
    def test_describe_change_set_with_verbose_flag(
        self, mock_simplify_change_set_description, mock_get_stack, mock_write
    ):
        stack = MagicMock(spec=Stack)
        stack.launch.return_value = StackStatus.COMPLETE
        mock_get_stack.return_value = stack
        stack.describe_change_set.return_value = "verbose"
        mock_simplify_change_set_description.return_value = "not_verbose"
        self.runner.invoke(
            cli, ["describe", "change-set", "dev/vpc.yaml", "cs1", "-v"]
        )
        stack.describe_change_set.assert_called_once_with("cs1")
        mock_write.assert_called_once_with("verbose", 'yaml')

    @patch('sceptre.cli.describe.write')
    @patch("sceptre.cli.describe.get_stack")
    def test_list_change_sets(self, mock_get_stack, mock_write):
        stack = MagicMock(spec=Stack)
        stack.list_change_sets.return_value = {
            "ResponseMetadata": "Test",
            "ChangeSets": "Test"
        }
        mock_get_stack.return_value = stack
        result = self.runner.invoke(
            cli, ["list", "change-sets", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        mock_write.assert_called_once_with({"ChangeSets": "Test"}, 'yaml')

    @patch('sceptre.cli.describe.write')
    @patch("sceptre.cli.describe.get_stack")
    def test_list_outputs(self, mock_get_stack, mock_write):
        stack = MagicMock(spec=Stack)
        outputs = [{"OutputKey": "Key", "OutputValue": "Value"}]
        stack.describe_outputs.return_value = outputs
        mock_get_stack.return_value = stack
        result = self.runner.invoke(
            cli, ["list", "outputs", "dev/vpc.yaml"]
        )
        assert result.exit_code == 0
        mock_write.assert_called_once_with(outputs, 'yaml')

    @patch('sceptre.cli.describe.write')
    @patch("sceptre.cli.describe.get_stack")
    def test_list_outputs_with_export(self, mock_get_stack, mock_write):
        stack = MagicMock(spec=Stack)
        outputs = [{"OutputKey": "Key", "OutputValue": "Value"}]
        stack.describe_outputs.return_value = outputs
        mock_get_stack.return_value = stack
        result = self.runner.invoke(
            cli, ["list", "outputs", "dev/vpc.yaml", "-e", "envvar"]
        )
        assert result.exit_code == 0
        mock_write.assert_called_once_with("export SCEPTRE_Key=Value")

    @patch("sceptre.cli.status.get_stack_and_env")
    def test_status_with_env(self, mock_get_stack_and_env):
        env = MagicMock(spec=Environment)
        mock_get_stack_and_env.return_value = (None, env)

        env.describe.return_value = {"stack": "status"}

        result = self.runner.invoke(cli, ["status", "dev"])
        assert result.exit_code == 0
        assert result.output == "stack: status\n\n"

    @patch("sceptre.cli.status.get_stack_and_env")
    def test_status_with_stack(self, mock_get_stack_and_env):
        stack = MagicMock(spec=Stack)
        env = MagicMock(spec=Environment)
        mock_get_stack_and_env.return_value = (stack, env)

        stack.get_status.return_value = "status"

        result = self.runner.invoke(cli, ["status", "dev"])
        assert result.exit_code == 0
        assert result.output == "status\n"

    def test_init_project_non_existant(self):
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

    def test_init_project_already_exist(self):
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

    @pytest.mark.parametrize(
        "path,recursive,return_stack,return_env,exception",
        [
            (
                "account/environment/region", False,
                False, False, RecursiveFlagMissingError
            ),
            (
                "account/environment/region", True,
                False, True, None
            ),
            (
                "account/environment/region/vpc.yaml", False,
                True, True, None
            ),
            (
                "account/environment/region/vpc.yaml", True,
                True, True, None
            ),
            (
                "account/environment/region/config.yaml", False,
                False, False, StackConfigNotFoundError
            ),
            (
                "account/environment/region/nonexistant.yaml", False,
                False, False, StackConfigNotFoundError
            )
        ]
    )
    @patch("sceptre.cli.helpers.Environment")
    def test_get_stack_and_env(
        self, mock_Environment, path, recursive,
        return_stack, return_env, exception
    ):
        ctx = MagicMock()
        ctx.obj = {
            "sceptre_dir": os.path.join(os.getcwd(), "tests", "fixtures"),
            "options": {}
        }
        mock_env = MagicMock(spec=Environment)
        mock_Environment.return_value = mock_env
        mock_env.stacks = {
            "vpc": sentinel.vpc_stack,
            "subnets": sentinel.vpc_stack,
            "security_groups": sentinel.vpc_stack,
        }

        try:
            stack, env = sceptre.cli.helpers.get_stack_and_env(
                ctx, path, recursive
            )
        except exception:
            pass

        if return_stack:
            assert stack == sentinel.vpc_stack
        if return_env:
            assert env == mock_env

    def test_setup_logging_with_debug(self):
        logger = sceptre.cli.helpers.setup_logging(True, False)
        assert logger.getEffectiveLevel() == logging.DEBUG
        assert logging.getLogger("botocore").getEffectiveLevel() == \
            logging.INFO

        # Silence logging for the rest of the tests
        logger.setLevel(logging.CRITICAL)

    def test_setup_logging_without_debug(self):
        logger = sceptre.cli.helpers.setup_logging(False, False)
        assert logger.getEffectiveLevel() == logging.INFO
        assert logging.getLogger("botocore").getEffectiveLevel() == \
            logging.CRITICAL

        # Silence logging for the rest of the tests
        logger.setLevel(logging.CRITICAL)

    @patch("sceptre.cli.click.echo")
    def test_write_with_yaml_format(self, mock_echo):
        sceptre.cli.helpers.write({"key": "value"}, "yaml")
        mock_echo.assert_called_once_with("key: value\n")

    @patch("sceptre.cli.click.echo")
    def test_write_with_json_format(self, mock_echo):
        sceptre.cli.helpers.write({"key": "value"}, "json")
        mock_echo.assert_called_once_with('{"key": "value"}')

    @patch("sceptre.cli.click.echo")
    def test_write_status_with_colour(self, mock_echo):
        sceptre.cli.helpers.write("stack: CREATE_COMPLETE", no_colour=False)
        mock_echo.assert_called_once_with(
            "stack: \x1b[32mCREATE_COMPLETE\x1b[0m"
        )

    @patch("sceptre.cli.click.echo")
    def test_write_status_without_colour(self, mock_echo):
        sceptre.cli.helpers.write("stack: CREATE_COMPLETE", no_colour=True)
        mock_echo.assert_called_once_with("stack: CREATE_COMPLETE")

    @patch("sceptre.cli.helpers.StackStatusColourer.colour")
    @patch("sceptre.cli.helpers.logging.Formatter.format")
    def test_ColouredFormatter_format_with_string(
            self, mock_format, mock_colour
    ):
        mock_format.return_value = sentinel.response
        mock_colour.return_value = sentinel.coloured_response
        coloured_formatter = sceptre.cli.helpers.ColouredFormatter()
        response = coloured_formatter.format("string")
        mock_format.assert_called_once_with("string")
        mock_colour.assert_called_once_with(sentinel.response)
        assert response == sentinel.coloured_response

    def test_CustomJsonEncoder_with_non_json_serialisable_object(self):
        encoder = sceptre.cli.helpers.CustomJsonEncoder()
        response = encoder.encode(datetime.datetime(2016, 5, 3))
        assert response == '"2016-05-03 00:00:00"'
