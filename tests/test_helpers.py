# -*- coding: utf-8 -*-

import os
import types

import pytest
from mock import sentinel, MagicMock

from sceptre.environment import Environment
from sceptre.helpers import get_subclasses
from sceptre.helpers import camel_to_snake_case
from sceptre.helpers import recurse_into_sub_environments
from sceptre.helpers import get_name_tuple
from sceptre.helpers import resolve_stack_name
from sceptre.helpers import get_external_stack_name
from sceptre.hooks import Hook
from sceptre.resolvers import Resolver


class TestHelpers(object):

    def test_get_subclasses(self):
        directory = os.path.join(os.getcwd(), "sceptre", "resolvers")
        classes = get_subclasses(Resolver, directory)

        # This is actually checking a property of the classes, which isn't
        # ideal but it's difficult to assert that the classes themselves are
        # the same.
        assert classes["environment_variable"].__name__ == \
            "EnvironmentVariable"
        assert classes["file_contents"].__name__ == \
            "FileContents"
        assert classes["stack_output_external"].__name__ == \
            "StackOutputExternal"
        assert classes["stack_output"].__name__ ==  \
            "StackOutput"
        assert len(classes) == 4

    def test_camel_to_snake_case(self):
        snake_case_string = camel_to_snake_case("Cmd")
        assert snake_case_string == "cmd"
        snake_case_string = camel_to_snake_case("ASGScalingProcesses")
        assert snake_case_string == "asg_scaling_processes"

    def test_recurse_into_sub_environments(self):
        environment = MagicMock(spec=Environment)
        environment.name = "environment"
        environment.sub_environments = []

        def do(self):
            return {self.name: sentinel.response}

        environment.do = types.MethodType(
            recurse_into_sub_environments(do),
            environment
        )

        response = environment.do()
        assert response == {"environment": sentinel.response}

    def test_recurse_into_sub_environments_with_non_leaf_object(self):
        class MockEnv(object):

            def __init__(self, name):
                self.name = name
                self.sub_environments = []

            @recurse_into_sub_environments
            def do(self):
                return {self.name: sentinel.response}

        mock_env = MockEnv("environment_1")

        # Add leaf sub-environments
        mock_env.sub_environments = [
            MockEnv("environment_2"), MockEnv("environment_3")
        ]

        response = mock_env.do()
        assert response == {
            "environment_1": sentinel.response,
            "environment_2": sentinel.response,
            "environment_3": sentinel.response
        }

    def test_get_name_tuple(self):
        result = get_name_tuple("dev/ew1/jump-host")
        assert result == ("dev", "ew1", "jump-host")

    def test_resolve_stack_name(self):
        result = resolve_stack_name("dev/ew1/subnet", "vpc")
        assert result == "dev/ew1/vpc"
        result = resolve_stack_name("dev/ew1/subnet", "prod/ue1/vpc")
        assert result == "prod/ue1/vpc"

    def test_get_external_stack_name(self):
        result = get_external_stack_name("prj", "dev/ew1/jump-host")
        assert result == "prj-dev-ew1-jump-host"

    def test_get_subclasses_with_invalid_directory(self):
        with pytest.raises(TypeError):
            get_subclasses(Hook, 1)
