# -*- coding: utf-8 -*-

from contextlib import contextmanager
from tempfile import mkdtemp
import shutil
import os
from mock import patch, sentinel, call, Mock, ANY
import pytest

from sceptre.config import Config
from sceptre.hooks import Hook
from sceptre.resolvers import Resolver
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

    @patch("sceptre.config.Config.add_hook_constructors")
    @patch("sceptre.config.Config.add_resolver_constructors")
    @patch("sceptre.config.Config._check_env_path_exists")
    def test_initialise_with_yaml_constructors(
        self, mock_check_env_path_exists,
        mock_add_resolver_constructors, mock_add_hook_constructors
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
        mock_add_resolver_constructors.assert_called_once_with(
            sentinel.environment_config, sentinel.connection_manager
        )
        mock_add_hook_constructors.assert_called_once_with(
            sentinel.environment_config, sentinel.connection_manager
        )

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
        user_variables = {"user_variable": "user_variable_value"}
        environment_config = {"region": "region"}
        self.config.read(user_variables, environment_config)

        assert self.config == {
            "parameters": {
                "param1": "user_variable_value",
                "param2": "environment_variable_value",
                "param3": "account",
                "param4": "environment",
                "param5": "region",
                "param6": "region"
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

    @patch("sceptre.config.get_subclasses")
    @patch("sceptre.config.yaml.SafeLoader.add_constructor")
    def test_add_yaml_constructors(
        self, mock_add_constructors, mock_get_subclasses
    ):
        mock_get_subclasses.return_value = {
            "class_1": sentinel.class_1,
            "class_2": sentinel.class_2,
            "class_3": sentinel.class_3,
        }
        directory = "directory/path"
        base_type = str
        function = Mock(return_value="class")
        self.config.add_yaml_constructors(directory, base_type, function)
        calls = [call(u'!class_1', "class"),
                 call(u'!class_2', "class"),
                 call(u'!class_3', "class")]
        mock_add_constructors.assert_has_calls(calls, any_order=True)

    @patch("sceptre.config.os.path.dirname")
    @patch("sceptre.config.Config.add_yaml_constructors")
    def test_add_resolver_constructors(
        self, mock_add_yaml_constructors, mock_dirname
    ):
        mock_dirname.return_value = "folder/with/file"
        environment_config = sentinel.environment_config
        connection_manager = sentinel.connection_manager
        self.config.add_resolver_constructors(
            environment_config, connection_manager
        )
        calls = [
            call("folder/with/file/resolvers", Resolver, ANY),
            call("sceptre_dir/resolvers", Resolver, ANY)
        ]
        mock_add_yaml_constructors.assert_has_calls(calls, any_order=False)

    @patch("sceptre.config.os.path.dirname")
    @patch("sceptre.config.Config.add_yaml_constructors")
    def test_add_hook_constructors(
        self, mock_add_yaml_constructors, mock_dirname
    ):
        mock_dirname.return_value = "folder/with/file"
        environment_config = sentinel.environment_config
        connection_manager = sentinel.connection_manager
        self.config.add_hook_constructors(
            environment_config, connection_manager
        )
        calls = [
            call("folder/with/file/hooks", Hook, ANY),
            call("sceptre_dir/hooks", Hook, ANY)
        ]
        mock_add_yaml_constructors.assert_has_calls(calls, any_order=False)
