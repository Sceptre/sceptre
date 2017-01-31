# -*- coding: utf-8 -*-

import tempfile
import pytest
from mock import sentinel

from sceptre.resolvers.project_variables import ProjectVariables


class TestProjectVariablesResolver(object):

    def setup_method(self, test_method):

        self.project_variables_resolver = ProjectVariables(
            environment_config=sentinel.environment_config,
            stack_config=sentinel.stack_config,
            connection_manager=sentinel.connection_manager,
            argument=None
        )
        self.project_variables_resolver.stack_config = sentinel.stack_config
        self.project_variables_resolver.stack_config.name = "Name"
        self.project_variables_resolver.environment_config = \
            sentinel.environment_config
        self.project_variables_resolver.environment_config.\
            environment_path = "dev/vpc"
        self.project_variables_resolver.environment_config.sceptre_dir = \
            sentinel.sceptre_dir

    def test_correct_return(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write("dev:\n    vpc:\n        Name: my_vpc")
            f.seek(0)
            self.project_variables_resolver.argument = f.name
            result = self.project_variables_resolver.resolve()
        assert result == "my_vpc"

    def test_with_non_existant_file_argument(self):
        with pytest.raises(IOError):
            self.project_variables_resolver.argument = "/non_existant_file"
            self.project_variables_resolver.resolve()

    def test_with_non_existant_key(self):
        with tempfile.NamedTemporaryFile() as f:
            f.write("dev:\n    vpc:\n        InvalidKey: my_vpc")
            f.seek(0)
            with pytest.raises(KeyError):
                self.project_variables_resolver.argument = f.name
                self.project_variables_resolver.resolve()
