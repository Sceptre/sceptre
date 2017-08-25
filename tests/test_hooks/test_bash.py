# -*- coding: utf-8 -*-

import pytest
from colorama import Fore, Style
from mock import patch

from sceptre.hooks.bash import Bash
from sceptre.exceptions import InvalidHookArgumentTypeError


class TestBash(object):
    def setup_method(self, test_method):
        self.mock_bash = Bash()

    @patch('warnings.warn')
    def test_run_with_non_str_argument(self, mock_warn):
        self.mock_bash.argument = None
        with pytest.raises(InvalidHookArgumentTypeError):
            self.mock_bash.run()
        mock_warn.assert_called_once_with(
            "{0}The bash hook has been deprecated, "
            "and will be removed in a later version of "
            "Sceptre. Use the cmd hook instead. "
            "Example: !cmd <command>{1}"
            .format(Fore.YELLOW, Style.RESET_ALL),
            DeprecationWarning
        )

    @patch('warnings.warn')
    @patch('sceptre.hooks.bash.subprocess.call')
    def test_run_with_str_argument(self, mock_call, mock_warn):
        Bash.ALLOW_COMMAND_ERROR = True
        self.mock_bash.argument = u'echo hello'
        self.mock_bash.run()
        mock_call.assert_called_once_with(['/bin/bash', '-c', 'echo hello'])
        mock_warn.assert_called_once_with(
            "{0}The bash hook has been deprecated, "
            "and will be removed in a later version of "
            "Sceptre. Use the cmd hook instead. "
            "Example: !cmd <command>{1}"
            .format(Fore.YELLOW, Style.RESET_ALL),
            DeprecationWarning
        )

    @patch('warnings.warn')
    @patch("sceptre.hooks.bash.subprocess.check_call")
    def test_bash_deny_command_error(self, mock_check_call, mock_warn):
        Bash.ALLOW_COMMAND_ERROR = False
        self.mock_bash.argument = u'echo hello'
        self.mock_bash.run()
        mock_check_call.assert_called_once_with(
            ['/bin/bash', '-c', 'echo hello'])
        mock_warn.assert_called_once_with(
            "{0}The bash hook has been deprecated, "
            "and will be removed in a later version of "
            "Sceptre. Use the cmd hook instead. "
            "Example: !cmd <command>{1}"
            .format(Fore.YELLOW, Style.RESET_ALL),
            DeprecationWarning
        )
