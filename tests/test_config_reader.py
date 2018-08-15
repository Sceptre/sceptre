# -*- coding: utf-8 -*-

import os
from mock import patch, sentinel
import pytest
import yaml
import errno

from sceptre.exceptions import VersionIncompatibleError
from sceptre.exceptions import ConfigFileNotFoundError
from sceptre.exceptions import InvalidSceptreDirectoryError

from freezegun import freeze_time
from click.testing import CliRunner
from sceptre.config.reader import ConfigReader


class TestConfigReader(object):
    @patch("sceptre.config.reader.ConfigReader._check_valid_sceptre_dir")
    def setup_method(self, test_method, mock_check_valid_sceptre_dir):
        self.runner = CliRunner()
        self.test_sceptre_directory = os.path.join(
            os.getcwd(), "tests", "fixtures"
        )

    def test_config_reader_correctly_initialised(self):
        config_reader = ConfigReader(self.test_sceptre_directory)
        assert config_reader.sceptre_dir == self.test_sceptre_directory

    def test_config_reader_with_invalid_path(self):
        with pytest.raises(InvalidSceptreDirectoryError):
            ConfigReader("/path/does/not/exist")

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
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
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

            config = ConfigReader(sceptre_dir).read(target)

            assert config == {
                "sceptre_dir": sceptre_dir,
                "stack_group_path": os.path.split(target)[0],
                "filepath": target
            }

    def test_read_reads_config_file_with_base_config(self):
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
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

            config = ConfigReader(sceptre_dir).read(
                "A/stack.yaml", base_config
            )

            assert config == {
                "sceptre_dir": sceptre_dir,
                "stack_group_path": "A",
                "config": "config",
                "base_config": "base_config"
            }

    def test_read_with_nonexistant_filepath(self):
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
            os.makedirs(config_dir)

            with pytest.raises(ConfigFileNotFoundError):
                ConfigReader(sceptre_dir).read("stack.yaml")

    def test_read_with_empty_config_file(self):
        config_reader = ConfigReader(self.test_sceptre_directory)
        config = config_reader.read(
          "account/stack-group/region/subnets.yaml"
        )
        assert config == {
            "sceptre_dir": self.test_sceptre_directory,
            "stack_group_path": "account/stack-group/region"
        }

    def test_read_with_templated_config_file(self):
        config_reader = ConfigReader(
            self.test_sceptre_directory,
            {"user_variable": "user_variable_value"}
        )
        config_reader.templating_vars["stack_group_config"] = {
            "region": "stack_group_region"
        }
        os.environ["TEST_ENV_VAR"] = "environment_variable_value"
        config = config_reader.read(
            "account/stack-group/region/security_groups.yaml"
        )
        # self.config.read({"user_variable": "user_variable_value"})
        assert config == {
            'sceptre_dir': config_reader.sceptre_dir,
            "stack_group_path": "account/stack-group/region",
            "parameters": {
                "param1": "user_variable_value",
                "param2": "environment_variable_value",
                "param3": "account",
                "param4": "stack-group",
                "param5": "region",
                "param6": "stack_group_region"
            }
        }

    def test_aborts_on_incompatible_version_requirement(self):
        config = {
            'require_version': '<0'
        }
        with pytest.raises(VersionIncompatibleError):
            ConfigReader(self.test_sceptre_directory)._check_version(config)

    @freeze_time("2012-01-01")
    @pytest.mark.parametrize("stack_name,config,expected", [
        (
            "name",
            {
                "template_bucket_name": "bucket-name",
                "template_key_prefix": "prefix"
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
    def test_construct_stack_with_valid_config(
        self, mock_Stack, mock_collect_s3_details
    ):
        mock_Stack.return_value = sentinel.stack
        mock_collect_s3_details.return_value = sentinel.s3_details
        config_reader = ConfigReader(self.test_sceptre_directory)
        stack = config_reader.construct_stack(
            "account/stack-group/region/vpc.yaml"
        )
        mock_Stack.assert_called_with(
                name="account/stack-group/region/vpc",
                project_code="account_project_code",
                template_path=os.path.join(
                    self.test_sceptre_directory, "path/to/template"
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
                stack_timeout=0
        )
        assert stack == sentinel.stack

    @pytest.mark.parametrize("filepaths,targets,results", [
        (
            ["A/1.yaml"], ["A"], [
                {
                    "A": {"stacks": ["A/1"], "stack_groups": {}}
                }
            ]
        ),
        (
            ["A/1.yaml", "A/2.yaml", "A/3.yaml"], ["A"], [
                {
                    "A": {
                        "stacks": ["A/3", "A/2", "A/1"],
                        "stack_groups": {}
                    }
                }
            ]
        ),
        (
            ["A/1.yaml", "A/A/1.yaml"], ["A", "A/A"], [
                {
                    "A": {
                        "stacks": [],
                        "stack_groups": {
                            "A/A": {
                                "stacks": ["A/A/1"],
                                "stack_groups": {}
                            },
                        }
                    }
                },
                {
                    "A/A": {"stacks": ["A/A/1"], "stack_groups": {}}
                }
            ]
        ),
        (
            ["A/1.yaml", "A/A/1.yaml", "A/A/2.yaml"], ["A", "A/A"], [
                {
                    "A": {
                        "stacks": [],
                        "stack_groups": {
                            "A/A": {
                              "stacks": ["A/A/1", "A/A/2"],
                              "stack_groups": {}
                            },
                        }
                    }
                },
                {
                    "A/A": {
                      "stacks": ["A/A/1", "A/A/2"], "stack_groups": {}
                    }
                }
                ]
        ),
        (
            ["A/A/1.yaml", "A/B/1.yaml"], ["A", "A/A", "A/B"], [
                {
                    "A": {
                        "stacks": [],
                        "stack_groups": {
                            "A/A": {
                              "stacks": ["A/A/1"], "stack_groups": {}
                            },
                            "A/B": {
                              "stacks": ["A/B/1"], "stack_groups": {}
                            }
                        }
                    }
                },
                {
                    "A/A": {"stacks": ["A/A/1"], "stack_groups":{}}
                },
                {
                    "A/B": {"stacks": ["A/B/1"], "stack_groups":{}}
                }
            ]
        )
    ])
    def test_construct_stack_group_with_valid_config(
        self, filepaths, targets, results
    ):
        with self.runner.isolated_filesystem():
            sceptre_dir = os.path.abspath('./example')
            config_dir = os.path.join(sceptre_dir, "config")
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

            config_reader = ConfigReader(sceptre_dir)

            def check_stack_group(stack_group, details):
                assert sorted(details["stacks"]) == sorted([
                    stack.name for stack in stack_group.stacks
                ])
                for sub_group in stack_group.sub_stack_groups:
                    sub_group_details =\
                      details["stack_groups"][sub_group.path]
                    check_stack_group(sub_group, sub_group_details)

            for i, target in enumerate(targets):
                stack_group =\
                  config_reader.construct_stack_group(target)
                expected = results[i]
                check_stack_group(
                  stack_group, expected[stack_group.path]
                )
