# -*- coding: utf-8 -*-

import os
from mock import patch, sentinel, MagicMock
import pytest
import yaml
import errno

from sceptre.context import SceptreContext
from sceptre.exceptions import DependencyDoesNotExistError
from sceptre.exceptions import VersionIncompatibleError
from sceptre.exceptions import ConfigFileNotFoundError
from sceptre.exceptions import InvalidSceptreDirectoryError
from sceptre.exceptions import InvalidConfigFileError

from freezegun import freeze_time
from click.testing import CliRunner
from sceptre.config.reader import ConfigReader


class TestConfigReader(object):
    @patch("sceptre.config.reader.ConfigReader._check_valid_project_path")
    def setup_method(self, test_method, mock_check_valid_project_path):
        self.runner = CliRunner()
        self.test_project_path = os.path.join(
            os.getcwd(), "tests", "fixtures"
        )
        self.context = SceptreContext(
            project_path=self.test_project_path,
            command_path="A"
        )

    def test_config_reader_correctly_initialised(self):
        config_reader = ConfigReader(self.context)
        assert config_reader.context == self.context

    def test_config_reader_with_invalid_path(self):
        with pytest.raises(InvalidSceptreDirectoryError):
            ConfigReader(SceptreContext("/path/does/not/exist", "example"))

    def create_project(self):
        """
        Creates a new random temporary directory with a config subdirectory
        """
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
        config_dir = os.path.join(project_path, "config")
        os.makedirs(config_dir)
        return (project_path, config_dir)

    def write_config(self, abs_path, config):
        """
        Writes a configuration dict to the specified path as YAML
        """
        if abs_path.endswith(".yaml"):
            dir_path = os.path.split(abs_path)[0]
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise

        with open(abs_path, 'w') as config_file:
            yaml.safe_dump(
                config, stream=config_file, default_flow_style=False
            )

    @pytest.mark.parametrize("filepaths,target", [
        (
            ["A/1.yaml"], "A/1.yaml"
        ),
        (
            ["A/1.yaml", "A/B/1.yaml"], "A/B/1.yaml"
        ),
        (
            ["A/1.yaml", "A/B/1.yaml", "A/B/C/1.yaml"], "A/B/C/1.yaml"
        )
    ])
    def test_read_reads_config_file(self, filepaths, target):
        project_path, config_dir = self.create_project()

        for rel_path in filepaths:
            config = {"filepath": rel_path}
            abs_path = os.path.join(config_dir, rel_path)
            self.write_config(abs_path, config)

        self.context.project_path = project_path
        config = ConfigReader(self.context).read(target)

        assert config == {
            "project_path": project_path,
            "stack_group_path": os.path.split(target)[0],
            "filepath": target
        }

    def test_read_reads_config_file_with_base_config(self):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
            config_dir = os.path.join(project_path, "config")
            stack_group_dir = os.path.join(config_dir, "A")

            os.makedirs(stack_group_dir)

            config = {"config": "config"}
            with open(os.path.join(stack_group_dir, "stack.yaml"), 'w') as\
                    config_file:
                yaml.safe_dump(
                    config, stream=config_file, default_flow_style=False
                )

            base_config = {
                "base_config": "base_config"
            }
            self.context.project_path = project_path
            config = ConfigReader(self.context).read(
                "A/stack.yaml", base_config
            )

            assert config == {
                "project_path": project_path,
                "stack_group_path": "A",
                "config": "config",
                "base_config": "base_config"
            }

    def test_read_with_nonexistant_filepath(self):
        project_path, config_dir = self.create_project()
        self.context.project_path = project_path
        with pytest.raises(ConfigFileNotFoundError):
            ConfigReader(self.context).read("stack.yaml")

    def test_read_with_empty_config_file(self):
        config_reader = ConfigReader(self.context)
        config = config_reader.read(
            "account/stack-group/region/subnets.yaml"
        )
        assert config == {
            "project_path": self.test_project_path,
            "stack_group_path": "account/stack-group/region"
        }

    def test_read_with_templated_config_file(self):
        self.context.user_variables = {"variable_key": "user_variable_value"}
        config_reader = ConfigReader(self.context)

        config_reader.templating_vars["stack_group_config"] = {
            "region": "region_region",
            "project_code": "account_project_code",
            "required_version": "'>1.0'",
            "template_bucket_name": "stack_group_template_bucket_name"
        }
        os.environ["TEST_ENV_VAR"] = "environment_variable_value"
        config = config_reader.read(
            "account/stack-group/region/security_groups.yaml"
        )

        assert config == {
            'project_path': self.context.project_path,
            "stack_group_path": "account/stack-group/region",
            "parameters": {
                "param1": "user_variable_value",
                "param2": "environment_variable_value",
                "param3": "region_region",
                "param4": "account_project_code",
                "param5": ">1.0",
                "param6": "stack_group_template_bucket_name"
            }
        }

    def test_aborts_on_incompatible_version_requirement(self):
        config = {
            'required_version': '<0'
        }
        with pytest.raises(VersionIncompatibleError):
            ConfigReader(self.context)._check_version(config)

    @freeze_time("2012-01-01")
    @pytest.mark.parametrize("stack_name,config,expected", [
        (
            "name",
            {
                "template_bucket_name": "bucket-name",
                "template_key_prefix": "prefix",
                "region": "eu-west-1"
            },
            {
                "bucket_name": "bucket-name",
                "bucket_key": "prefix/name/2012-01-01-00-00-00-000000Z.json"
            }
        ),
        (
            "name",
            {
                "template_bucket_name": "bucket-name",
                "region": "eu-west-1"
            },
            {
                "bucket_name": "bucket-name",
                "bucket_key": "name/2012-01-01-00-00-00-000000Z.json"
            }
        ),
        (
            "name",
            {
                "template_bucket_name": "bucket-name",
            },
            {
                "bucket_name": "bucket-name",
                "bucket_key": "name/2012-01-01-00-00-00-000000Z.json"
            }
        ),
        (
            "name", {}, None
        )
    ]
    )
    def test_collect_s3_details(self, stack_name, config, expected):
        details = ConfigReader._collect_s3_details(stack_name, config)
        assert details == expected

    @patch("sceptre.config.reader.ConfigReader._collect_s3_details")
    @patch("sceptre.config.reader.Stack")
    def test_construct_stacks_constructs_stack(
        self, mock_Stack, mock_collect_s3_details
    ):
        mock_Stack.return_value = sentinel.stack
        sentinel.stack.dependencies = []

        mock_collect_s3_details.return_value = sentinel.s3_details
        self.context.project_path = os.path.abspath("tests/fixtures-vpc")
        self.context.command_path = "account/stack-group/region/vpc.yaml"
        stacks = ConfigReader(self.context).construct_stacks()
        mock_Stack.assert_any_call(
            name="account/stack-group/region/vpc",
            project_code="account_project_code",
            template_path=os.path.join(
                self.context.project_path, "templates/path/to/template"
            ),
            region="region_region",
            profile="account_profile",
            parameters={"param1": "val1"},
            sceptre_user_data={},
            hooks={},
            s3_details=sentinel.s3_details,
            dependencies=["child/level", "top/level"],
            iam_role=None,
            role_arn=None,
            protected=False,
            tags={},
            external_name=None,
            notifications=None,
            on_failure=None,
            stack_timeout=0,
            required_version='>1.0',
            template_bucket_name='stack_group_template_bucket_name',
            template_key_prefix=None,
            stack_group_config={
                "custom_key": "custom_value"
            }
        )

        assert stacks == ({sentinel.stack}, {sentinel.stack})

    @pytest.mark.parametrize("command_path,filepaths,expected_stacks,expected_command_stacks,full_scan", [
        (
            "",
            ["A/1.yaml"],
            {"A/1"},
            {"A/1"},
            False
        ),
        (
            "",
            ["A/1.yaml", "A/2.yaml", "A/3.yaml"],
            {"A/3", "A/2", "A/1"},
            {"A/3", "A/2", "A/1"},
            False
        ),
        (
            "",
            ["A/1.yaml", "A/A/1.yaml"],
            {"A/1", "A/A/1"},
            {"A/1", "A/A/1"},
            False
        ),
        (
            "",
            ["A/1.yaml", "A/A/1.yaml", "A/A/2.yaml"],
            {"A/1", "A/A/1", "A/A/2"},
            {"A/1", "A/A/1", "A/A/2"},
            False
        ),
        (
            "",
            ["A/A/1.yaml", "A/B/1.yaml"],
            {"A/A/1", "A/B/1"},
            {"A/A/1", "A/B/1"},
            False
        ),
        (
            "Abd",
            ["Abc/1.yaml", "Abd/1.yaml"],
            {"Abd/1"},
            {"Abd/1"},
            False
        ),
        (
            "Abd",
            ["Abc/1.yaml", "Abd/Abc/1.yaml", "Abd/2.yaml"],
            {"Abd/2", "Abd/Abc/1"},
            {"Abd/2", "Abd/Abc/1"},
            False
        ),
        (
            "Abd/Abc",
            ["Abc/1.yaml", "Abd/Abc/1.yaml", "Abd/2.yaml"],
            {"Abd/Abc/1"},
            {"Abd/Abc/1"},
            False
        ),
        (
            "Ab",
            ["Abc/1.yaml", "Abd/1.yaml"],
            set(),
            set(),
            False
        ),
        (
            "Abd/Abc",
            ["Abc/1.yaml", "Abd/Abc/1.yaml", "Abd/2.yaml"],
            {"Abc/1", "Abd/Abc/1", "Abd/2"},
            {"Abd/Abc/1"},
            True
        ),
    ])
    def test_construct_stacks_with_valid_config(
        self, command_path, filepaths, expected_stacks, expected_command_stacks, full_scan
    ):
        project_path, config_dir = self.create_project()

        for rel_path in filepaths:

            config = {
                "region": "region",
                "project_code": "project_code",
                "template_path": rel_path
            }

            abs_path = os.path.join(config_dir, rel_path)
            self.write_config(abs_path, config)

        self.context.project_path = project_path
        self.context.command_path = command_path
        self.context.full_scan = full_scan
        config_reader = ConfigReader(self.context)
        all_stacks, command_stacks = config_reader.construct_stacks()
        assert {str(stack) for stack in all_stacks} == expected_stacks
        assert {str(stack) for stack in command_stacks} == expected_command_stacks

    @pytest.mark.parametrize("filepaths, del_key", [
        (["A/1.yaml"], "project_code"),
        (["A/1.yaml"], "region"),
        (["A/1.yaml"], "template_path"),
    ])
    def test_missing_attr(
        self, filepaths, del_key
    ):
        project_path, config_dir = self.create_project()

        for rel_path in filepaths:

            config = {
                "project_code": "project_code",
                "region": "region",
                "template_path": rel_path
            }
            # Delete the mandatory key to be tested.
            del config[del_key]

            abs_path = os.path.join(config_dir, rel_path)
            self.write_config(abs_path, config)

        self.context.project_path = project_path
        try:
            config_reader = ConfigReader(self.context)
            all_stacks, command_stacks = config_reader.construct_stacks()
        except InvalidConfigFileError as e:
            # Test that the missing key is reported.
            assert del_key in str(e)
        except Exception:
            raise
        else:
            assert False

    @pytest.mark.parametrize("filepaths, dependency", [
        (["A/1.yaml", "B/1.yaml", "B/2.yaml"], "A/1.yaml"),
        (["A/1.yaml", "B/1.yaml", "B/2.yaml"], "B/1.yaml"),
    ])
    def test_existing_dependency(
        self, filepaths, dependency
    ):
        project_path, config_dir = self.create_project()

        for rel_path in filepaths:
            # Set up config with reference to an existing stack
            config = {
                "project_code": "project_code",
                "region": "region",
                "template_path": rel_path,
                "dependencies": [dependency]
            }

            abs_path = os.path.join(config_dir, rel_path)
            self.write_config(abs_path, config)

        self.context.project_path = project_path
        try:
            config_reader = ConfigReader(self.context)
            all_stacks, command_stacks = config_reader.construct_stacks()
        except Exception:
            raise
        else:
            assert True

    @pytest.mark.parametrize("filepaths, dependency", [
        (["A/1.yaml", "B/1.yaml", "B/2.yaml"], "A/2.yaml"),
        (["A/1.yaml", "B/1.yaml", "B/2.yaml"], "1.yaml"),
    ])
    def test_missing_dependency(
        self, filepaths, dependency
    ):
        project_path, config_dir = self.create_project()

        for rel_path in filepaths:
            # Set up config with reference to non-existing stack
            config = {
                "project_code": "project_code",
                "region": "region",
                "template_path": rel_path,
                "dependencies": [dependency]
            }

            abs_path = os.path.join(config_dir, rel_path)
            self.write_config(abs_path, config)

        self.context.project_path = project_path
        try:
            config_reader = ConfigReader(self.context)
            all_stacks, command_stacks = config_reader.construct_stacks()
        except DependencyDoesNotExistError as e:
            # Test that the missing dependency is reported.
            assert dependency in str(e)
        except Exception:
            raise
        else:
            assert False

    def test_resolve_node_tag(self):
        mock_loader = MagicMock(yaml.Loader)
        mock_loader.resolve.return_value = "new_tag"

        mock_node = MagicMock(yaml.Node)
        mock_node.tag = "old_tag"
        mock_node.value = "String"

        config_reader = ConfigReader(self.context)
        new_node = config_reader.resolve_node_tag(mock_loader, mock_node)

        assert new_node.tag == 'new_tag'
