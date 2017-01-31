# -*- coding: utf-8 -*-

import pytest
from mock import patch

from sceptre.hooks.bash import Bash
from sceptre.exceptions import InvalidHookArgumentTypeError


class TestBash(object):
    def setup_method(self, test_method):
        self.mock_bash = Bash()

    def test_run_with_non_str_argument(self):
        self.mock_bash.argument = None
        with pytest.raises(InvalidHookArgumentTypeError):
            self.mock_bash.run()

    @patch('sceptre.hooks.bash.subprocess.call')
    def test_run_with_str_argument(self, mock_call):
        Bash.ALLOW_COMMAND_ERROR = True
        self.mock_bash.argument = u"echo hello"
        self.mock_bash.run()
        mock_call.assert_called_once_with(['/bin/bash', '-c', "echo hello"])

    @patch("sceptre.hooks.bash.subprocess.check_call")
    def test_bash_deny_command_error(self, mock_check_call):
        Bash.ALLOW_COMMAND_ERROR = False
        self.mock_bash.argument = u"echo hello"
        self.mock_bash.run()
        mock_check_call.assert_called_once_with(
            ['/bin/bash', '-c', "echo hello"])
