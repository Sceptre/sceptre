"""Tests for src/template_handler/formatted_yaml.py"""
from unittest.mock import patch, mock_open

import pytest

from sceptre.template_handlers.formatted_yaml import FormattedYaml

# pylint: disable=missing-function-docstring


@pytest.fixture(name="formatted_yaml")
def fixture_formatted_yaml():
    return FormattedYaml("test")


class TestFormattedYaml:
    """
    TestFormattedYaml class.

    This class is used for testing the functionality of the
    FormattedYaml class.
    """

    def test_format_yaml_content__remove_trailing_whitespaces_and_blank_lines(
        self, formatted_yaml
    ):
        with patch("sceptre.template_handlers.file.File.handle") as mock_handle:
            mock_handle.return_value = "  key1: value1  \n\n  key2: value2  \n\n"
            result = formatted_yaml.handle()

        expected_result = "  key1: value1\n  key2: value2\n"

        assert result == expected_result

    def test_format_yaml_content__add_blank_lines(self, formatted_yaml):
        with patch("sceptre.template_handlers.file.File.handle") as mock_handle:
            mock_handle.return_value = "  key1: value1\n  key2: value2"
            result = formatted_yaml.handle()

        expected_result = "  key1: value1\n  key2: value2\n"

        assert result == expected_result

    def test_format_yaml__directives(self, formatted_yaml):
        with patch("sceptre.template_handlers.file.File.handle") as mock_handle:
            mock_handle.return_value = "---\nkey1: value1\nkey2: value2"
            result = formatted_yaml.handle()

        expected_result = "---\n\nkey1: value1\n\nkey2: value2\n"

        assert result == expected_result

    def test_format_yaml__directives__ignores_certain_fields(self, formatted_yaml):
        with patch("sceptre.template_handlers.file.File.handle") as mock_handle:
            mock_handle.return_value = (
                "---\n"
                "AWSTemplateFormatVersion: '2010-09-09'\n"
                "Description: Foo\n"
                "key1: value1\n"
                "key2: value2"
            )
            result = formatted_yaml.handle()

        expected_result = (
            "---\n"
            "AWSTemplateFormatVersion: '2010-09-09'\n"
            "Description: Foo\n\n"
            "key1: value1\n\n"
            "key2: value2\n"
        )

        assert result == expected_result


class TestFile:
    """
    TestFile class.

    This class is used for testing the functionality of the underlying
    TestFile class.
    """

    @pytest.mark.parametrize(
        "project_path,path,output_path",
        [
            (
                "my_project_dir",
                "my.template.yaml",
                "my_project_dir/templates/my.template.yaml",
            ),  # NOQA
            (
                "/src/my_project_dir",
                "my.template.yaml",
                "/src/my_project_dir/templates/my.template.yaml",
            ),  # NOQA
            (
                "my_project_dir",
                "/src/my_project_dir/templates/my.template.yaml",
                "/src/my_project_dir/templates/my.template.yaml",
            ),  # NOQA
            (
                "/src/my_project_dir",
                "/src/my_project_dir/templates/my.template.yaml",
                "/src/my_project_dir/templates/my.template.yaml",
            ),  # NOQA
        ],
    )
    @patch("builtins.open", new_callable=mock_open, read_data="some_data")
    def test_handler_open(self, mocked_open, project_path, path, output_path):
        template_handler = FormattedYaml(
            name="file_handler",
            arguments={"path": path},
            stack_group_config={"project_path": project_path},
        )
        template_handler.handle()
        mocked_open.assert_called_with(output_path)

    @pytest.mark.parametrize(
        "project_path,path,output_path",
        [
            (
                "my_project_dir",
                "my.template.yaml.j2",
                "my_project_dir/templates/my.template.yaml.j2",
            ),  # NOQA
            (
                "/src/my_project_dir",
                "my.template.yaml.j2",
                "/src/my_project_dir/templates/my.template.yaml.j2",
            ),  # NOQA
            (
                "my_project_dir",
                "/src/my_project_dir/templates/my.template.yaml.j2",
                "/src/my_project_dir/templates/my.template.yaml.j2",
            ),  # NOQA
            (
                "/src/my_project_dir",
                "/src/my_project_dir/templates/my.template.yaml.j2",
                "/src/my_project_dir/templates/my.template.yaml.j2",
            ),  # NOQA
        ],
    )
    @patch("sceptre.template_handlers.helper.render_jinja_template")
    def test_handler_render(self, mocked_render, project_path, path, output_path):
        template_handler = FormattedYaml(
            name="file_handler",
            arguments={"path": path},
            stack_group_config={"project_path": project_path},
        )
        template_handler.handle()
        mocked_render.assert_called_with(output_path, {"sceptre_user_data": None}, {})

    @pytest.mark.parametrize(
        "project_path,path,output_path",
        [
            (
                "my_project_dir",
                "my.template.yaml.py",
                "my_project_dir/templates/my.template.yaml.py",
            ),  # NOQA
            (
                "/src/my_project_dir",
                "my.template.yaml.py",
                "/src/my_project_dir/templates/my.template.yaml.py",
            ),  # NOQA
            (
                "my_project_dir",
                "/src/my_project_dir/templates/my.template.yaml.py",
                "/src/my_project_dir/templates/my.template.yaml.py",
            ),  # NOQA
            (
                "/src/my_project_dir",
                "/src/my_project_dir/templates/my.template.yaml.py",
                "/src/my_project_dir/templates/my.template.yaml.py",
            ),  # NOQA
        ],
    )
    @patch("sceptre.template_handlers.helper.call_sceptre_handler")
    def test_handler_handler(self, mocked_handler, project_path, path, output_path):
        template_handler = FormattedYaml(
            name="file_handler",
            arguments={"path": path},
            stack_group_config={"project_path": project_path},
        )
        template_handler.handle()
        mocked_handler.assert_called_with(output_path, None)
