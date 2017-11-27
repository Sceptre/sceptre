# -*- coding: utf-8 -*-

from mock import patch

from sceptre.resolvers.environment_variable import EnvironmentVariable


class TestEnvironmentVariableResolver(object):

    def setup_method(self, test_method):
        self.environment_variable_resolver = EnvironmentVariable(
            argument=None
        )

    @patch("sceptre.resolvers.environment_variable.os")
    def test_resolving_with_set_environment_variable(self, mock_os):
        mock_os.environ = {"VARIABLE": "value"}
        self.environment_variable_resolver.argument = "VARIABLE"
        response = self.environment_variable_resolver.resolve()
        assert response == "value"

    def test_resolving_with_unset_environment_variable(self):
        self.environment_variable_resolver.argument = "UNSETVARIABLE"
        response = self.environment_variable_resolver.resolve()
        assert response is None

    def test_resolving_with_environment_variable_name_as_none(self):
        self.environment_variable_resolver.argument = None
        response = self.environment_variable_resolver.resolve()
        assert response is None
