from os import path
from mock import sentinel
import importlib

from sceptre.context import SceptreContext


class TestSceptreContext(object):

    def setup_method(self, test_method):
        self.context = SceptreContext(
            project_path="project_path/to/sceptre",
            command_path="command/path",
            user_variables={},
            options={},
            output_format="json",
            no_colour=True,
            ignore_dependencies=False
        )

    def test_context_with_path(self):
        context = SceptreContext(
            project_path="project_path/to/sceptre",
            command_path="command-path",
            user_variables=sentinel.user_variables,
            options=sentinel.options,
            output_format=sentinel.output_format,
            no_colour=sentinel.no_colour,
            ignore_dependencies=sentinel.ignore_dependencies
        )

        sentinel.project_path = "project_path/to/sceptre"
        assert context.project_path == sentinel.project_path

    def test_full_config_path_returns_correct_path(self):
        context = SceptreContext(
            project_path="project_path",
            command_path="command-path",
            user_variables=sentinel.user_variables,
            options=sentinel.options,
            output_format=sentinel.output_format,
            no_colour=sentinel.no_colour,
            ignore_dependencies=sentinel.ignore_dependencies
        )

        full_config_path = path.join("project_path", self.context.config_path)
        assert context.full_config_path() == full_config_path

    def test_full_command_path_returns_correct_path(self):
        context = SceptreContext(
            project_path="project_path",
            command_path="command",
            user_variables=sentinel.user_variables,
            options=sentinel.options,
            output_format=sentinel.output_format,
            no_colour=sentinel.no_colour,
            ignore_dependencies=sentinel.ignore_dependencies
        )
        full_command_path = path.join("project_path",
                                      self.context.config_path,
                                      "command")

        assert context.full_command_path() == full_command_path

    def test_full_templates_path_returns_correct_path(self):
        context = SceptreContext(
            project_path="project_path",
            command_path="command",
            user_variables=sentinel.user_variables,
            options=sentinel.options,
            output_format=sentinel.output_format,
            no_colour=sentinel.no_colour,
            ignore_dependencies=sentinel.ignore_dependencies
        )
        full_templates_path = path.join("project_path", self.context.templates_path)
        assert context.full_templates_path() == full_templates_path

    def test_context_repr(self):
        assert self.context.__repr__() == \
            "sceptre.context.SceptreContext(" \
            "project_path='project_path/to/sceptre', " \
            "command_path='command/path', " \
            "user_variables={}, "\
            "options={}, " \
            "output_format='json', " \
            "no_colour=True, " \
            "ignore_dependencies=False" \
            ")"

    def test_repr_can_eval_correctly(self):
        sceptre = importlib.import_module('sceptre')
        mock = importlib.import_module('mock')
        evaluated_context = eval(
            repr(self.context),
            {
                'sceptre': sceptre,
                'sentinel': mock.mock.sentinel
            }
        )
        assert isinstance(evaluated_context, SceptreContext)
        assert evaluated_context.__eq__(self.context)

    def test_context_hash(self):
        assert hash(self.context) == self.context.__hash__()

    def test_command_path_is_stack_with_valid_stack(self):
        self.context.project_path = "tests/fixtures"
        self.context.command_path = "account/stack-group/region/vpc.yaml"
        assert self.context.command_path_is_stack()

    def test_command_path_is_stack_with_directory(self):
        self.context.project_path = "tests/fixtures"
        self.context.command_path = "account/stack-group/region"
        assert self.context.command_path_is_stack() is False
