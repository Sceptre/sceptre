# -*- coding: utf-8 -*-

from contextlib import contextmanager
from tempfile import mkdtemp
import os
from mock import patch, sentinel
import pytest
import shutil
import yaml

from sceptre.config import Config
from sceptre.exceptions import ConfigItemNotFoundError
from sceptre.exceptions import EnvironmentPathNotFoundError
from sceptre.exceptions import VersionIncompatibleError


class TestConfig(object):

    @patch("sceptre.config.Config._check_env_path_exists")
    def setup_method(self, test_method, mock_check_env_path_exists):
        self.config = Config(
            sceptre_dir="sceptre_dir",
            environment_path="environment_path",
            base_file_name="config"
        )

    @contextmanager
    def _create_temp_dir(self):
        temp_directory = mkdtemp()
        yield temp_directory
        shutil.rmtree(temp_directory)

    def test_config_correctly_initialised(self):
        assert self.config.sceptre_dir == "sceptre_dir"
        assert self.config.environment_path == "environment_path"
        assert self.config.name == "config"

    @patch("sceptre.config.Config._check_env_path_exists")
    def test_initialise_with_yaml_constructors(
        self, mock_check_env_path_exists
    ):
        config = Config.with_yaml_constructors(
            sceptre_dir="sceptre_dir",
            environment_path="environment_path",
            base_file_name="config",
            environment_config=sentinel.environment_config,
            connection_manager=sentinel.connection_manager
        )
        assert config.sceptre_dir == "sceptre_dir"
        assert config.environment_path == "environment_path"
        assert config.name == "config"
        assert "!stack_output" in yaml.SafeLoader.yaml_constructors
        assert "!stack_output_external" in yaml.SafeLoader.yaml_constructors
        assert "!environment_variable" in yaml.SafeLoader.yaml_constructors
        assert "!file_contents" in yaml.SafeLoader.yaml_constructors
        assert "!cmd" in yaml.SafeLoader.yaml_constructors
        assert "!asg_scheduled_actions" in yaml.SafeLoader.yaml_constructors

    def test_get_attribute_with_valid_attribute(self):
        self.config["key"] = "value"
        assert self.config["key"] == "value"

    def test_get_attribute_with_invalid_attribute(self):
        with pytest.raises(ConfigItemNotFoundError):
            self.config["this_key_does_not_exist"]

    def test_read_reads_single_config_file(self):
        self.config.sceptre_dir = os.path.join(
            os.getcwd(), "tests", "fixtures"
        )
        self.config.environment_path = os.path.join(
            "account", "environment", "region"
        )
        self.config.name = "vpc"
        self.config.read()
        assert self.config == {
            'parameters': [{'param1': 'val1'}],
            'dependencies': [],
            'template_path': 'path/to/template'
        }

    def test_read_with_empty_config_file(self):
        self.config.sceptre_dir = os.path.join(
            os.getcwd(), "tests", "fixtures"
        )
        self.config.environment_path = os.path.join(
            "account", "environment", "region"
        )
        self.config.name = "subnets"

        self.config.read()
        assert self.config == {
            'dependencies': []
        }

    def test_read_cascades_config(self):
        self.config.sceptre_dir = os.path.join(
            os.getcwd(), "tests", "fixtures"
        )
        self.config.environment_path = os.path.join(
            "account", "environment", "region"
        )
        self.config.name = "config"
        self.config.read()
        assert self.config == {
            "region": "region_region",
            "template_bucket_name": "environment_template_bucket_name",
            "project_code": "account_project_code",
            "iam_role": "account_iam_role",
            "require_version": ">=0a",
            'dependencies': []
        }

    def test_read_with_templated_config_file(self):
        self.config.sceptre_dir = os.path.join(
            os.getcwd(), "tests", "fixtures"
        )
        self.config.environment_path = os.path.join(
            "account", "environment", "region"
        )
        self.config.name = "security_groups"
        os.environ["TEST_ENV_VAR"] = "environment_variable_value"
        self.config.read({"user_variable": "user_variable_value"})

        assert self.config == {
            "parameters": {
                "param1": "user_variable_value",
                "param2": "environment_variable_value",
                "param3": "account",
                "param4": "environment",
                "param5": "region"
            },
            'dependencies': []
        }

    def test_check_env_path_exists_with_valid_dir(self):
        with self._create_temp_dir() as temp_dir:
            self.config._check_env_path_exists(temp_dir)

    def test_check_env_path_exists_with_invalid_dir(self):
        with pytest.raises(EnvironmentPathNotFoundError):
            self.config._check_env_path_exists(
                "/this/directory/does/not/exist"
            )

    def test_aborts_on_incompatible_version_requirement(self):
        self.config['require_version'] = '<0'
        with pytest.raises(VersionIncompatibleError):
            self.config._check_version()
