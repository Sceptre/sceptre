# -*- coding: utf-8 -*-

import errno
import os
import string
from unittest.mock import patch, sentinel, MagicMock, ANY

import pytest
import yaml

from click.testing import CliRunner
from freezegun import freeze_time
from glob import glob

from sceptre.config.reader import ConfigReader
from sceptre.context import SceptreContext
from sceptre.resolvers.stack_attr import StackAttr

from sceptre.exceptions import (
    DependencyDoesNotExistError,
    VersionIncompatibleError,
    ConfigFileNotFoundError,
    InvalidSceptreDirectoryError,
    InvalidConfigFileError,
    SceptreException,
)


class TestConfigReader(object):
    @patch("sceptre.config.reader.ConfigReader._check_valid_project_path")
    def setup_method(self, test_method, mock_check_valid_project_path):
        self.runner = CliRunner()
        self.test_project_path = os.path.join(os.getcwd(), "tests", "fixtures")
        self.context = SceptreContext(
            project_path=self.test_project_path,
            command_path="A",
            command_params={
                "yes": True,
                "path": "A.yaml",
                "prune": False,
                "disable_rollback": None,
            },
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
            project_path = os.path.abspath("./example")
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

        with open(abs_path, "w") as config_file:
            yaml.safe_dump(config, stream=config_file, default_flow_style=False)

    @pytest.mark.parametrize(
        "filepaths,target",
        [
            (["A/1.yaml"], "A/1.yaml"),
            (["A/1.yaml", "A/B/1.yaml"], "A/B/1.yaml"),
            (["A/1.yaml", "A/B/1.yaml", "A/B/C/1.yaml"], "A/B/C/1.yaml"),
        ],
    )
    def test_read_reads_config_file(self, filepaths, target):
        project_path, config_dir = self.create_project()

        for rel_path in filepaths:
            config = {"filepath": rel_path}
            abs_path = os.path.join(config_dir, rel_path)
            self.write_config(abs_path, config)

        self.context.project_path = project_path
        config = ConfigReader(self.context)._read(target)

        assert config == {
            "project_path": project_path,
            "stack_group_path": os.path.split(target)[0],
            "filepath": target,
        }

    def test_read_nested_configs(self):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath("./example")
            config_dir = os.path.join(project_path, "config")
            stack_group_dir_a = os.path.join(config_dir, "A")
            stack_group_dir_b = os.path.join(stack_group_dir_a, "B")
            stack_group_dir_c = os.path.join(stack_group_dir_b, "C")

            os.makedirs(stack_group_dir_c)
            config_filename = "config.yaml"

            config_a = {"keyA": "A", "shared": "A"}
            with open(
                os.path.join(stack_group_dir_a, config_filename), "w"
            ) as config_file:
                yaml.safe_dump(config_a, stream=config_file, default_flow_style=False)

            config_b = {"keyB": "B", "parent": "{{ keyA }}", "shared": "B"}
            with open(
                os.path.join(stack_group_dir_b, config_filename), "w"
            ) as config_file:
                yaml.safe_dump(config_b, stream=config_file, default_flow_style=False)

            config_c = {"keyC": "C", "parent": "{{ keyB }}", "shared": "C"}
            with open(
                os.path.join(stack_group_dir_c, config_filename), "w"
            ) as config_file:
                yaml.safe_dump(config_c, stream=config_file, default_flow_style=False)

            self.context.project_path = project_path
            reader = ConfigReader(self.context)

            config_a = reader._read("A/config.yaml")

            assert config_a == {
                "project_path": project_path,
                "stack_group_path": "A",
                "keyA": "A",
                "shared": "A",
            }

            config_b = reader._read("A/B/config.yaml")

            assert config_b == {
                "project_path": project_path,
                "stack_group_path": "A/B",
                "keyA": "A",
                "keyB": "B",
                "shared": "B",
                "parent": "A",
            }

            config_c = reader._read("A/B/C/config.yaml")

            assert config_c == {
                "project_path": project_path,
                "stack_group_path": "A/B/C",
                "keyA": "A",
                "keyB": "B",
                "keyC": "C",
                "shared": "C",
                "parent": "B",
            }

    def test_read_reads_config_file_with_base_config(self):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath("./example")
            config_dir = os.path.join(project_path, "config")
            stack_group_dir = os.path.join(config_dir, "A")

            os.makedirs(stack_group_dir)

            config = {"config": "config"}
            with open(os.path.join(stack_group_dir, "stack.yaml"), "w") as config_file:
                yaml.safe_dump(config, stream=config_file, default_flow_style=False)

            base_config = {"base_config": "base_config"}
            self.context.project_path = project_path
            config = ConfigReader(self.context)._read("A/stack.yaml", base_config)

            assert config == {
                "project_path": project_path,
                "stack_group_path": "A",
                "config": "config",
                "base_config": "base_config",
            }

    def test_read_with_nonexistant_filepath(self):
        project_path, config_dir = self.create_project()
        self.context.project_path = project_path
        with pytest.raises(ConfigFileNotFoundError):
            ConfigReader(self.context)._read("stack.yaml")

    def test_read_with_empty_config_file(self):
        config_reader = ConfigReader(self.context)
        config = config_reader._read("account/stack-group/region/subnets.yaml")
        assert config == {
            "project_path": self.test_project_path,
            "stack_group_path": "account/stack-group/region",
        }

    def test_read_with_templated_config_file(self):
        self.context.user_variables = {"variable_key": "user_variable_value"}
        config_reader = ConfigReader(self.context)

        config_reader.templating_vars["stack_group_config"] = {
            "region": "region_region",
            "project_code": "account_project_code",
            "required_version": "'>1.0'",
            "template_bucket_name": "stack_group_template_bucket_name",
        }
        os.environ["TEST_ENV_VAR"] = "environment_variable_value"
        config = config_reader._read("account/stack-group/region/security_groups.yaml")

        assert config == {
            "project_path": self.context.project_path,
            "stack_group_path": "account/stack-group/region",
            "parameters": {
                "param1": "user_variable_value",
                "param2": "environment_variable_value",
                "param3": "region_region",
                "param4": "account_project_code",
                "param5": ">1.0",
                "param6": "stack_group_template_bucket_name",
            },
        }

    def test_aborts_on_incompatible_version_requirement(self):
        config = {"required_version": "<0"}
        with pytest.raises(VersionIncompatibleError):
            ConfigReader(self.context)._check_version(config)

    @freeze_time("2012-01-01")
    @pytest.mark.parametrize(
        "stack_name,config,expected",
        [
            (
                "name",
                {
                    "template_bucket_name": "bucket-name",
                    "template_key_prefix": "prefix",
                    "region": "eu-west-1",
                },
                {
                    "bucket_name": "bucket-name",
                    "bucket_key": "prefix/name/2012-01-01-00-00-00-000000Z.json",
                },
            ),
            (
                "name",
                {"template_bucket_name": "bucket-name", "region": "eu-west-1"},
                {
                    "bucket_name": "bucket-name",
                    "bucket_key": "name/2012-01-01-00-00-00-000000Z.json",
                },
            ),
            (
                "name",
                {
                    "template_bucket_name": "bucket-name",
                },
                {
                    "bucket_name": "bucket-name",
                    "bucket_key": "name/2012-01-01-00-00-00-000000Z.json",
                },
            ),
            ("name", {}, None),
        ],
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
            template_path=None,
            template_handler_config={"path": "path/to/template"},
            region="region_region",
            profile="account_profile",
            parameters={"param1": "val1"},
            sceptre_user_data={},
            hooks={},
            s3_details=sentinel.s3_details,
            dependencies=["top/level", "child/level"],
            iam_role=None,
            sceptre_role=None,
            iam_role_session_duration=None,
            sceptre_role_session_duration=None,
            role_arn=None,
            cloudformation_service_role=None,
            protected=False,
            tags={},
            external_name=None,
            notifications=None,
            on_failure=None,
            disable_rollback=False,
            stack_timeout=0,
            required_version=">1.0",
            template_bucket_name="stack_group_template_bucket_name",
            template_key_prefix=None,
            ignore=False,
            obsolete=False,
            stack_group_config={
                "project_path": self.context.project_path,
                "custom_key": "custom_value",
            },
            config=ANY,
        )

        assert stacks == ({sentinel.stack}, {sentinel.stack})

    @pytest.mark.parametrize(
        "command_path,filepaths,expected_stacks,expected_command_stacks,full_scan",
        [
            ("", ["A/1.yaml"], {"A/1"}, {"A/1"}, False),
            (
                "",
                ["A/1.yaml", "A/2.yaml", "A/3.yaml"],
                {"A/3", "A/2", "A/1"},
                {"A/3", "A/2", "A/1"},
                False,
            ),
            ("", ["A/1.yaml", "A/A/1.yaml"], {"A/1", "A/A/1"}, {"A/1", "A/A/1"}, False),
            (
                "",
                ["A/1.yaml", "A/A/1.yaml", "A/A/2.yaml"],
                {"A/1", "A/A/1", "A/A/2"},
                {"A/1", "A/A/1", "A/A/2"},
                False,
            ),
            (
                "",
                ["A/A/1.yaml", "A/B/1.yaml"],
                {"A/A/1", "A/B/1"},
                {"A/A/1", "A/B/1"},
                False,
            ),
            ("Abd", ["Abc/1.yaml", "Abd/1.yaml"], {"Abd/1"}, {"Abd/1"}, False),
            (
                "Abd",
                ["Abc/1.yaml", "Abd/Abc/1.yaml", "Abd/2.yaml"],
                {"Abd/2", "Abd/Abc/1"},
                {"Abd/2", "Abd/Abc/1"},
                False,
            ),
            (
                "Abd/Abc",
                ["Abc/1.yaml", "Abd/Abc/1.yaml", "Abd/2.yaml"],
                {"Abd/Abc/1"},
                {"Abd/Abc/1"},
                False,
            ),
            ("Ab", ["Abc/1.yaml", "Abd/1.yaml"], set(), set(), False),
            (
                "Abd/Abc",
                ["Abc/1.yaml", "Abd/Abc/1.yaml", "Abd/2.yaml"],
                {"Abc/1", "Abd/Abc/1", "Abd/2"},
                {"Abd/Abc/1"},
                True,
            ),
        ],
    )
    def test_construct_stacks_with_valid_config(
        self,
        command_path,
        filepaths,
        expected_stacks,
        expected_command_stacks,
        full_scan,
    ):
        project_path, config_dir = self.create_project()

        for rel_path in filepaths:
            config = {
                "region": "region",
                "project_code": "project_code",
                "template": {
                    "path": rel_path,
                },
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

    def test_construct_stacks_with_disable_rollback_command_param(self):
        project_path, config_dir = self.create_project()

        rel_path = "A/1.yaml"
        config = {
            "region": "region",
            "project_code": "project_code",
            "template": {"path": rel_path},
        }

        abs_path = os.path.join(config_dir, rel_path)
        self.write_config(abs_path, config)
        self.context.project_path = project_path
        self.context.command_params["disable_rollback"] = True
        config_reader = ConfigReader(self.context)
        all_stacks, command_stacks = config_reader.construct_stacks()
        assert list(all_stacks)[0].disable_rollback

    def test_construct_stacks_with_disable_rollback_in_stack_config(self):
        project_path, config_dir = self.create_project()

        rel_path = "A/1.yaml"
        config = {
            "region": "region",
            "project_code": "project_code",
            "template": {"path": rel_path},
            "disable_rollback": True,
        }

        abs_path = os.path.join(config_dir, rel_path)
        self.write_config(abs_path, config)
        self.context.project_path = project_path
        config_reader = ConfigReader(self.context)
        all_stacks, command_stacks = config_reader.construct_stacks()
        assert list(all_stacks)[0].disable_rollback

    @pytest.mark.parametrize(
        "filepaths, del_key",
        [
            (["A/1.yaml"], "project_code"),
            (["A/1.yaml"], "region"),
        ],
    )
    def test_missing_attr(self, filepaths, del_key):
        project_path, config_dir = self.create_project()

        for rel_path in filepaths:
            config = {
                "project_code": "project_code",
                "region": "region",
                "template_path": rel_path,
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

    @pytest.mark.parametrize(
        "filepaths, dependency",
        [
            (["A/1.yaml", "B/1.yaml", "B/2.yaml"], "A/1.yaml"),
            (["A/1.yaml", "B/1.yaml", "B/2.yaml"], "B/1.yaml"),
        ],
    )
    def test_existing_dependency(self, filepaths, dependency):
        project_path, config_dir = self.create_project()

        for rel_path in filepaths:
            # Set up config with reference to an existing stack
            config = {
                "project_code": "project_code",
                "region": "region",
                "template": {"path": rel_path},
                "dependencies": [dependency],
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

    @pytest.mark.parametrize(
        "filepaths, dependency",
        [
            (["A/1.yaml", "B/1.yaml", "B/2.yaml"], "A/2.yaml"),
            (["A/1.yaml", "B/1.yaml", "B/2.yaml"], "1.yaml"),
        ],
    )
    def test_missing_dependency(self, filepaths, dependency):
        project_path, config_dir = self.create_project()

        for rel_path in filepaths:
            # Set up config with reference to non-existing stack
            config = {
                "project_code": "project_code",
                "region": "region",
                "template": {"path": rel_path},
                "dependencies": [dependency],
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

    @pytest.mark.parametrize(
        "filepaths, dependency, parent_config_path",
        [
            (["A/1.yaml", "A/2.yaml", "B/1.yaml"], "B/1.yaml", "A/config.yaml"),
            (["A/1.yaml", "A/2.yaml"], "A/1.yaml", "A/config.yaml"),
        ],
    )
    def test_inherited_dependency_already_resolved(
        self, filepaths, dependency, parent_config_path
    ):
        project_path, config_dir = self.create_project()
        parent_config = {"dependencies": [dependency]}
        abs_path = os.path.join(config_dir, parent_config_path)
        self.write_config(abs_path, parent_config)

        for rel_path in filepaths:
            # Set up config with reference to an existing stack
            config = {
                "project_code": "project_code",
                "region": "region",
                "template": {"path": rel_path},
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

    def test_resolve_node_tag(self):
        mock_loader = MagicMock(yaml.Loader)
        mock_loader.resolve.return_value = "new_tag"

        mock_node = MagicMock(yaml.Node)
        mock_node.tag = "old_tag"
        mock_node.value = "String"

        config_reader = ConfigReader(self.context)
        new_node = config_reader.resolve_node_tag(mock_loader, mock_node)

        assert new_node.tag == "new_tag"

    def test_render__missing_config_file__returns_none(self):
        config_reader = ConfigReader(self.context)
        directory_path = "configs"
        basename = "missing_config.yaml"
        stack_group_config = {}

        result = config_reader._render(directory_path, basename, stack_group_config)
        assert result is None

    def test_render__existing_config_file__returns_dict(self):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath("./example")
            config_dir = os.path.join(project_path, "config")
            directory_path = os.path.join(config_dir, "configs")

            os.makedirs(directory_path)

            basename = "existing_config.yaml"
            stack_group_config = {}

            test_config_path = os.path.join(directory_path, basename)
            test_config_content = "key: value"

            with open(test_config_path, "w") as file:
                file.write(test_config_content)

            self.context.project_path = project_path
            config_reader = ConfigReader(self.context)

            result = config_reader._render("configs", basename, stack_group_config)

            assert result == {"key": "value"}

    def test_render__invalid_jinja_template__raises_and_creates_debug_file(self):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath("./example")
            config_dir = os.path.join(project_path, "config")
            directory_path = os.path.join(config_dir, "configs")

            os.makedirs(directory_path)

            basename = "invalid_jinja.yaml"
            stack_group_config = {}

            test_config_path = os.path.join(directory_path, basename)
            test_config_content = "key: {{ invalid_var }}"

            with open(test_config_path, "w") as file:
                file.write(test_config_content)

            self.context.project_path = project_path
            config_reader = ConfigReader(self.context)

            pattern = f"{os.path.join('configs', basename)} - .*"
            with pytest.raises(SceptreException, match=pattern):
                config_reader._render("configs", basename, stack_group_config)
                assert len(glob("/tmp/vars_*")) == 1

    def test_render_invalid_yaml__raises_and_creates_debug_file(self):
        with self.runner.isolated_filesystem():
            project_path = os.path.abspath("./example")
            config_dir = os.path.join(project_path, "config")
            directory_path = os.path.join(config_dir, "configs")

            os.makedirs(directory_path)

            basename = "invalid_yaml.yaml"
            stack_group_config = {}

            test_config_path = os.path.join(directory_path, basename)
            test_config_content = "{ key: value"

            with open(test_config_path, "w") as file:
                file.write(test_config_content)

            self.context.project_path = project_path
            config_reader = ConfigReader(self.context)

            with pytest.raises(ValueError, match="Error parsing .*"):
                config_reader._render("configs", basename, stack_group_config)
                assert len(glob("/tmp/rendered_*")) == 1

    @pytest.mark.parametrize(
        "config_key", ("parameters", "sceptre_user_data", "stack_tags")
    )
    @pytest.mark.parametrize(
        "inheritance_at,values,expected_value",
        [
            (
                0,
                [{"a": "a"}, {"b": "b"}, {"c": "c"}, {}],
                {"a": "a", "b": "b", "c": "c"},
            ),
            (
                1,
                [{"a": "a"}, {"b": "b"}, {"c": "c"}, {}],
                {"a": "a", "b": "b", "c": "c"},
            ),
            (
                0,
                [{"a": "a"}, {"b": "b"}, {"c": "c"}, {"d": "d"}],
                {"a": "a", "b": "b", "c": "c", "d": "d"},
            ),
            (
                2,
                [{"a": "a"}, {"b": "b"}, {"c": "c"}, {}],
                {"b": "b", "c": "c"},
            ),
            (
                3,
                [{"a": "a"}, {"b": "b"}, {"c": "c"}, {}],
                {"c": "c"},
            ),
            (
                99,
                [{"a": "a"}, {"b": "b"}, {"c": "c"}, {}],
                {},
            ),
            (
                99,
                [{"a": "a"}, {"b": "b"}, {"c": "c"}, {"d": "d"}],
                {"d": "d"},
            ),
            (
                3,
                [{"a": "a"}, {"b": "b"}, {"c": "c"}, {"c": "x", "d": "d"}],
                {"c": "x", "d": "d"},
            ),
        ],
    )
    def test_inheritance_strategy_override_dict_merge(
        self,
        config_key,
        inheritance_at,
        values,
        expected_value,
    ):
        project_path, config_dir = self.create_project()
        filepaths = [
            "/".join(string.ascii_uppercase[:i]) + "/config.yaml"
            for i in range(1, len(values))
        ]
        filepaths.append(
            "/".join(string.ascii_uppercase[: len(values) - 1]) + "/1.yaml"
        )

        for i, (stack_path, stack_values) in enumerate(zip(filepaths, values)):
            params = {config_key: stack_values}
            if i == inheritance_at:
                params[f"{config_key}_inheritance"] = "merge"
            config = {
                "region": "region",
                "project_code": "project_code",
                "template": {
                    "path": stack_path,
                },
                **params,
            }
            abs_path = os.path.join(config_dir, stack_path)
            self.write_config(abs_path, config)

        self.context.project_path = project_path
        config_reader = ConfigReader(self.context)
        stack = list(config_reader.construct_stacks()[0])[-1]
        stack_key = StackAttr.STACK_ATTR_MAP.get(config_key, config_key)
        assert getattr(stack, stack_key) == expected_value

    # "dependencies" is not included here as it has other tests and testing
    # it requires configs to be created which makes setup harder.
    @pytest.mark.parametrize("config_key", ("hooks", "notifications"))
    @pytest.mark.parametrize(
        "inheritance_at,values,expected_value",
        [
            (0, [["a"], ["b"], ["c"], []], ["a", "b", "c"]),
            (1, [["a"], ["b"], ["c"], []], ["a", "b", "c"]),
            (2, [["a"], ["b"], ["c"], []], ["b", "c"]),
            (3, [["a"], ["b"], ["c"], ["d"]], ["c", "d"]),
            (99, [["a"], ["b"], ["c"], ["d"]], ["d"]),
        ],
    )
    def test_inheritance_strategy_override_list_join(
        self,
        config_key,
        inheritance_at,
        values,
        expected_value,
    ):
        project_path, config_dir = self.create_project()
        filepaths = [
            "/".join(string.ascii_uppercase[:i]) + "/config.yaml"
            for i in range(1, len(values))
        ]
        filepaths.append(
            "/".join(string.ascii_uppercase[: len(values) - 1]) + "/1.yaml"
        )

        for i, (stack_path, stack_values) in enumerate(zip(filepaths, values)):
            params = {config_key: stack_values}
            if i == inheritance_at:
                params[f"{config_key}_inheritance"] = "merge"
            config = {
                "region": "region",
                "project_code": "project_code",
                "template": {
                    "path": stack_path,
                },
                **params,
            }
            abs_path = os.path.join(config_dir, stack_path)
            self.write_config(abs_path, config)

        self.context.project_path = project_path
        config_reader = ConfigReader(self.context)
        stack = list(config_reader.construct_stacks()[0])[-1]
        stack_key = StackAttr.STACK_ATTR_MAP.get(config_key, config_key)
        assert getattr(stack, stack_key) == expected_value

    @pytest.mark.parametrize(
        "config_key,strategy",
        (
            ("hooks", "foo"),
            ("hooks", "deepcopy"),
            ("hooks", "child_or_parent"),
            ("stack_tags", "foo"),
        ),
    )
    def test_inheritance_strategy_override_errors_on_invalid_strategy(
        self, config_key, strategy
    ):
        project_path, config_dir = self.create_project()
        stack_path = "A/1.yaml"
        config = {
            "region": "region",
            "project_code": "project_code",
            "template": {
                "path": stack_path,
            },
            f"{config_key}_inheritance": strategy,
        }
        abs_path = os.path.join(config_dir, stack_path)
        self.write_config(abs_path, config)
        self.context.project_path = project_path
        config_reader = ConfigReader(self.context)
        with pytest.raises(SceptreException):
            config_reader.construct_stacks()
