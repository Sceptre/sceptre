# -*- coding: utf-8 -*-

import os
from mock import patch, sentinel
import pytest
import yaml
import errno

from sceptre.context import SceptreContext
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
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
            config_dir = os.path.join(project_path, "config")
            os.makedirs(config_dir)

            for rel_path in filepaths:
                abs_path = os.path.join(config_dir, rel_path)
                if not os.path.exists(os.path.dirname(abs_path)):
                    try:
                        os.makedirs(os.path.dirname(abs_path))
                    except OSError as exc:
                        if exc.errno != errno.EEXIST:
                            raise

                config = {"filepath": rel_path}
                with open(abs_path, 'w') as config_file:
                    yaml.safe_dump(
                        config, stream=config_file, default_flow_style=False
                    )

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
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
            config_dir = os.path.join(project_path, "config")
            os.makedirs(config_dir)
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
                "bucket_key": "prefix/name/2012-01-01-00-00-00-000000Z.json",
                "bucket_region": "eu-west-1",
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
                "bucket_key": "name/2012-01-01-00-00-00-000000Z.json",
                "bucket_region": "eu-west-1",
            }
        ),
        (
                "name",
                {
                    "template_bucket_name": "bucket-name",
                },
                {
                    "bucket_name": "bucket-name",
                    "bucket_key": "name/2012-01-01-00-00-00-000000Z.json",
                    "bucket_region": None,
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

    @pytest.mark.parametrize("filepaths,expected_stacks", [
        (["A/1.yaml"], {"A/1"}),
        (["A/1.yaml", "A/2.yaml", "A/3.yaml"], {"A/3", "A/2", "A/1"}),
        (["A/1.yaml", "A/A/1.yaml"], {"A/1", "A/A/1"}),
        (["A/1.yaml", "A/A/1.yaml", "A/A/2.yaml"], {"A/1", "A/A/1", "A/A/2"}),
        (["A/A/1.yaml", "A/B/1.yaml"], {"A/A/1", "A/B/1"})
    ])
    def test_construct_stacks_with_valid_config(
        self, filepaths, expected_stacks
    ):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
            config_dir = os.path.join(project_path, "config")
            os.makedirs(config_dir)

            for rel_path in filepaths:
                abs_path = os.path.join(config_dir, rel_path)
                dir_path = abs_path
                if abs_path.endswith(".yaml"):
                    dir_path = os.path.split(abs_path)[0]
                if not os.path.exists(dir_path):
                    try:
                        os.makedirs(dir_path)
                    except OSError as exc:
                        if exc.errno != errno.EEXIST:
                            raise

                config = {
                    "region": "region",
                    "project_code": "project_code",
                    "template_path": rel_path
                }
                with open(abs_path, 'w') as config_file:
                    yaml.safe_dump(
                        config, stream=config_file, default_flow_style=False
                    )

            self.context.project_path = project_path
            config_reader = ConfigReader(self.context)
            all_stacks, command_stacks = config_reader.construct_stacks()
            assert {str(stack) for stack in all_stacks} == expected_stacks

    @pytest.mark.parametrize("filepaths,target,del_key", [
        (["A/1.yaml"], "A/1.yaml", "project_code"),
        (["A/1.yaml"], "A/1.yaml", "region"),
        (["A/1.yaml"], "A/1.yaml", "template_path"),
    ])
    def test_missing_attr(
        self, filepaths, target, del_key
    ):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath('./example')
            config_dir = os.path.join(project_path, "config")
            os.makedirs(config_dir)

            self.context.project_path = project_path

            for rel_path in filepaths:
                abs_path = os.path.join(config_dir, rel_path)
                dir_path = abs_path
                if abs_path.endswith(".yaml"):
                    dir_path = os.path.split(abs_path)[0]
                if not os.path.exists(dir_path):
                    try:
                        os.makedirs(dir_path)
                    except OSError as exc:
                        if exc.errno != errno.EEXIST:
                            raise

                config = {
                    "project_code": "project_code",
                    "region": "region",
                    "template_path": rel_path
                }

                # Delete the mandatory key to be tested.
                del config[del_key]

                with open(abs_path, 'w') as config_file:
                    yaml.safe_dump(
                        config, stream=config_file, default_flow_style=False
                    )

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
