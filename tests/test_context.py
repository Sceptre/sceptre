from os import path
from unittest.mock import sentinel
from sceptre.context import SceptreContext


class TestSceptreContext(object):
    def setup_method(self, test_method):
        self.templates_path = "templates"
        self.config_path = "config"
        self.config_file = "config.yaml"

    def test_context_with_path(self):
        self.context = SceptreContext(
            project_path="project_path/to/sceptre",
            command_path="command-path",
            command_params=sentinel.command_params,
            user_variables=sentinel.user_variables,
            options=sentinel.options,
            output_format=sentinel.output_format,
            no_colour=sentinel.no_colour,
            ignore_dependencies=sentinel.ignore_dependencies,
        )

        sentinel.project_path = "project_path/to/sceptre"
        assert self.context.project_path.replace(path.sep, "/") == sentinel.project_path

    def test_full_config_path_returns_correct_path(self):
        context = SceptreContext(
            project_path="project_path",
            command_path="command-path",
            command_params=sentinel.command_params,
            user_variables=sentinel.user_variables,
            options=sentinel.options,
            output_format=sentinel.output_format,
            no_colour=sentinel.no_colour,
            ignore_dependencies=sentinel.ignore_dependencies,
        )

        full_config_path = path.join("project_path", self.config_path)
        assert context.full_config_path() == full_config_path

    def test_full_command_path_returns_correct_path(self):
        context = SceptreContext(
            project_path="project_path",
            command_path="command",
            command_params=sentinel.command_params,
            user_variables=sentinel.user_variables,
            options=sentinel.options,
            output_format=sentinel.output_format,
            no_colour=sentinel.no_colour,
            ignore_dependencies=sentinel.ignore_dependencies,
        )
        full_command_path = path.join("project_path", self.config_path, "command")

        assert context.full_command_path() == full_command_path

    def test_full_templates_path_returns_correct_path(self):
        context = SceptreContext(
            project_path="project_path",
            command_path="command",
            command_params=sentinel.command_params,
            user_variables=sentinel.user_variables,
            options=sentinel.options,
            output_format=sentinel.output_format,
            no_colour=sentinel.no_colour,
            ignore_dependencies=sentinel.ignore_dependencies,
        )
        full_templates_path = path.join("project_path", self.templates_path)
        assert context.full_templates_path() == full_templates_path

    def test_clone__returns_full_clone_of_context(self):
        context = SceptreContext(
            project_path="project_path",
            command_path="command",
            command_params={"params": "variables"},
            user_variables={"user": "variables"},
            options={"hello": "there"},
            output_format=sentinel.output_format,
            no_colour=sentinel.no_colour,
            ignore_dependencies=sentinel.ignore_dependencies,
        )
        clone = context.clone()
        assert clone is not context
        assert clone.project_path == context.project_path
        assert clone.command_path == context.command_path
        assert clone.user_variables == context.user_variables
        assert clone.user_variables is not context.user_variables
        assert clone.options == context.options
        assert clone.options is not context.options
        assert clone.output_format == context.output_format
        assert clone.no_colour == context.no_colour
        assert clone.ignore_dependencies == context.ignore_dependencies
