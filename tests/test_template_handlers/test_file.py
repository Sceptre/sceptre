# -*- coding: utf-8 -*-

import pytest

from sceptre.template_handlers.file import File
from unittest.mock import patch, mock_open, call


class TestFile(object):

    @pytest.mark.parametrize("project_path,path,output_path", [
        ("my_project_dir",      "my.template.yaml",                               "my_project_dir/templates/my.template.yaml"),
        ("/src/my_project_dir", "my.template.yaml",                               "/src/my_project_dir/templates/my.template.yaml"),
        ("my_project_dir",      "/src/my_project_dir/templates/my.template.yaml", "/src/my_project_dir/templates/my.template.yaml"),
        ("/src/my_project_dir", "/src/my_project_dir/templates/my.template.yaml", "/src/my_project_dir/templates/my.template.yaml"),
    ])
    @patch("builtins.open", new_callable=mock_open, read_data="some_data")
    def test_handler_open(self, mocked_open, project_path, path, output_path):
        template_handler = File(
            name="file_handler",
            arguments={"path": path},
            stack_group_config={"project_path": project_path}
        )
        result = template_handler.handle()
        mocked_open.assert_called_with(output_path)

    @pytest.mark.parametrize("project_path,path,output_path", [
        ("my_project_dir",      "my.template.yaml.j2",                               "my_project_dir/templates/my.template.yaml.j2"),
        ("/src/my_project_dir", "my.template.yaml.j2",                               "/src/my_project_dir/templates/my.template.yaml.j2"),
        ("my_project_dir",      "/src/my_project_dir/templates/my.template.yaml.j2", "/src/my_project_dir/templates/my.template.yaml.j2"),
        ("/src/my_project_dir", "/src/my_project_dir/templates/my.template.yaml.j2", "/src/my_project_dir/templates/my.template.yaml.j2"),
    ])
    @patch("sceptre.template_handlers.helper.render_jinja_template")
    def test_handler_render(self, mocked_render, project_path, path, output_path):
        template_handler = File(
            name="file_handler",
            arguments={"path": path},
            stack_group_config={"project_path": project_path}
        )
        result = template_handler.handle()
        mocked_render.assert_called_with(output_path, {"sceptre_user_data": None}, {})

    @pytest.mark.parametrize("project_path,path,output_path", [
        ("my_project_dir",      "my.template.yaml.py",                               "my_project_dir/templates/my.template.yaml.py"),
        ("/src/my_project_dir", "my.template.yaml.py",                               "/src/my_project_dir/templates/my.template.yaml.py"),
        ("my_project_dir",      "/src/my_project_dir/templates/my.template.yaml.py", "/src/my_project_dir/templates/my.template.yaml.py"),
        ("/src/my_project_dir", "/src/my_project_dir/templates/my.template.yaml.py", "/src/my_project_dir/templates/my.template.yaml.py"),
    ])
    @patch("sceptre.template_handlers.helper.call_sceptre_handler")
    def test_handler_handler(self, mocked_handler, project_path, path, output_path):
        template_handler = File(
            name="file_handler",
            arguments={"path": path},
            stack_group_config={"project_path": project_path}
        )
        result = template_handler.handle()
        mocked_handler.assert_called_with(output_path, None)
