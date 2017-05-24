# -*- coding: utf-8 -*-

import pytest
from mock import patch

from sceptre.hooks.cmd import Cmd
from sceptre.exceptions import InvalidHookArgumentTypeError


class TestCmd(object):
    def setup_method(self, test_method):
        self.cmd = Cmd()

    def test_run_with_non_str_argument(self):
        self.cmd.argument = None
        with pytest.raises(InvalidHookArgumentTypeError):
            self.cmd.run()

    @patch('sceptre.hooks.bash.subprocess.check_call')
    def test_run_with_str_argument(self, mock_call):
        self.cmd.argument = u"echo hello"
        self.cmd.run()
        mock_call.assert_called_once_with(['/bin/bash', '-c', "echo hello"])
