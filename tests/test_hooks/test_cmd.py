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

    def test_null_input_raises_exception(self):
        self.cmd.argument = None
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    def test_empty_string_raises_exception(self):
        self.cmd.argument = ""
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    def test_list_raises_exception(self):
        self.cmd.argument = ["echo", "hello"]
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    def test_dict_without_executable_raises_exception(self):
        self.cmd.argument = {"args": "echo hello"}
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    def test_dict_without_args_raises_exception(self):
        self.cmd.argument = {"executable": "/bin/bash"}
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    def test_dict_with_list_args_raises_exception(self):
        self.cmd.argument = {"args": ["echo", "hello"], "executable": "/bin/bash"}
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    def test_dict_with_list_executable_raises_exception(self):
        self.cmd.argument = {"args": "echo hello", "executable": ["/bin/bash"]}
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    def test_input_exception_reprs_input(self):
        import datetime

        self.cmd.argument = datetime.date(2023, 8, 31)
        exception_message = (
            r"A cmd hook requires either a string argument or an object with "
            r"args and executable keys with string values\. You gave "
            r"datetime.date\(2023, 8, 31\)\."
        )
        with pytest.raises(InvalidHookArgumentTypeError, match=exception_message):
            self.cmd.run()

    def test_zero_exit_returns(self):
        self.cmd.argument = "exit 0"
        self.cmd.run()

    def test_nonzero_exit_raises_exception(self):
        self.cmd.argument = "exit 1"
        with pytest.raises(CalledProcessError):
            self.cmd.run()

    def test_command_writes_to_stdout(self, capfd):
        self.cmd.argument = "echo hello"
        self.cmd.run()
        cap = capfd.readouterr()
        assert cap.out.strip() == "hello"
        assert cap.err.strip() == ""

    def test_shell_error_writes_to_stderr(self, capfd):
        self.cmd.argument = "missing_command"
        try:
            self.cmd.run()
        except CalledProcessError:
            cap = capfd.readouterr()
            assert cap.out.strip() == ""
            assert "missing_command: not found" in cap.err

    def test_default_shell_is_sh(self, capfd):
        self.cmd.argument = "echo $0"
        self.cmd.run()
        cap = capfd.readouterr()
        assert cap.out.strip() == "/bin/sh"
        assert cap.err.strip() == ""

    def test_executable_sets_the_shell(self, capfd):
        self.cmd.argument = {"args": "echo $0", "executable": "/bin/bash"}
        self.cmd.run()
        cap = capfd.readouterr()
        assert cap.out.strip() == "/bin/bash"
        assert cap.err.strip() == ""
