# -*- coding: utf-8 -*-
import subprocess
from unittest.mock import patch, Mock

import pytest

from sceptre.exceptions import InvalidHookArgumentTypeError
from sceptre.hooks.cmd import Cmd
from sceptre.stack import Stack


class TestCmd(object):
    def setup_method(self, test_method):
        self.stack = Mock(Stack)
        self.cmd = Cmd(stack=self.stack)

    def test_run_with_non_str_argument(self):
        self.cmd.argument = None
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    @patch("sceptre.hooks.cmd.subprocess.check_call")
    def test_run_with_str_argument(self, mock_call):
        self.cmd.argument = "echo hello"
        self.cmd.run()
        expected_envs = (
            self.stack.connection_manager.create_session_environment_variables.return_value
        )
        mock_call.assert_called_once_with("echo hello", shell=True, env=expected_envs)

    @patch("sceptre.hooks.cmd.subprocess.check_call")
    def test_run_with_erroring_command(self, mock_call):
        mock_call.side_effect = subprocess.CalledProcessError(1, "echo")
        self.cmd.argument = "echo hello"
        with pytest.raises(subprocess.CalledProcessError):
            self.cmd.run()
