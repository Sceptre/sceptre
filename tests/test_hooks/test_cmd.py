# -*- coding: utf-8 -*-
from subprocess import CalledProcessError

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
        self.cmd = Cmd(stack=self.stack)

    def test_run_with_non_str_argument(self):
        self.cmd.argument = None
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    def test_run_with_str_argument(self, capfd):
        self.cmd.argument = "echo hello"
        self.cmd.run()
        cap = capfd.readouterr()
        assert cap.out.strip() == "hello"
        assert cap.err.strip() == ""

    def test_run_with_erroring_command(self):
        self.cmd.argument = "missing_command_that_causes_shell_error"
        with pytest.raises(CalledProcessError):
            self.cmd.run()
