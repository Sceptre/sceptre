# -*- coding: utf-8 -*-
from subprocess import CalledProcessError
from unittest.mock import Mock
import pytest

from sceptre.exceptions import InvalidHookArgumentTypeError
from sceptre.hooks.cmd import Cmd
from sceptre.stack import Stack


class TestCmd(object):
    def setup_method(self, test_method):
        self.stack = Stack(
            "stack1",
            "project1",
            "region1",
            template_handler_config={"template": "path.yaml"},
        )

        # Otherwise the test works only when the environment variables already
        # set a valid AWS session.
        self.stack.connection_manager.create_session_environment_variables = Mock(
            return_value={}
        )

        self.cmd = Cmd(stack=self.stack)

    def test_run_with_null(self):
        self.cmd.argument = None
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    def test_run_with_correct_command(self, capfd):
        self.cmd.argument = "echo hello"
        self.cmd.run()
        cap = capfd.readouterr()
        assert cap.out.strip() == "hello"
        assert cap.err.strip() == ""

    def test_run_with_erroring_command(self):
        self.cmd.argument = "missing_command_that_causes_shell_error"
        with pytest.raises(CalledProcessError):
            self.cmd.run()

    def test_run_with_command_and_executable(self):
        # TODO: Choose how to test this.
        # Mock subprocess and check that executable message is sent?
        # Spy Popen and check executable?
        pytest.fail()
