# -*- coding: utf-8 -*-
from subprocess import CalledProcessError
from unittest.mock import Mock
import pytest

from sceptre.exceptions import InvalidHookArgumentTypeError
from sceptre.hooks.cmd import Cmd
from sceptre.stack import Stack


@pytest.fixture()
def stack():
    stack = Stack(
        "stack1",
        "project1",
        "region1",
        template_handler_config={"template": "path.yaml"},
    )

    # Otherwise the test works only when the environment variables already set a
    # valid AWS session.
    stack.connection_manager.create_session_environment_variables = Mock(
        return_value={}
    )

    return stack


def test_null_input_raises_exception(stack):
    with pytest.raises(InvalidHookArgumentTypeError):
        Cmd(None, stack).run()


def test_empty_string_raises_exception(stack):
    with pytest.raises(InvalidHookArgumentTypeError):
        Cmd("", stack).run()


def test_list_raises_exception(stack):
    with pytest.raises(InvalidHookArgumentTypeError):
        Cmd(["echo", "hello"], stack).run()


def test_dict_without_executable_raises_exception(stack):
    with pytest.raises(InvalidHookArgumentTypeError):
        Cmd({"args": "echo hello"}, stack).run()


def test_dict_without_args_raises_exception(stack):
    with pytest.raises(InvalidHookArgumentTypeError):
        Cmd({"executable": "/bin/bash"}, stack).run()


def test_dict_with_list_args_raises_exception(stack):
    with pytest.raises(InvalidHookArgumentTypeError):
        Cmd({"args": ["echo", "hello"], "executable": "/bin/bash"}, stack).run()


def test_dict_with_list_executable_raises_exception(stack):
    with pytest.raises(InvalidHookArgumentTypeError):
        Cmd({"args": "echo hello", "executable": ["/bin/bash"]}, stack).run()


def test_input_exception_reprs_input(stack):
    import datetime

    exception_message = (
        r"A cmd hook requires either a string argument or an object with args and "
        r"executable keys with string values\. You gave datetime.date\(2023, 8, 31\)\."
    )
    with pytest.raises(InvalidHookArgumentTypeError, match=exception_message):
        Cmd(datetime.date(2023, 8, 31), stack).run()


def test_zero_exit_returns(stack):
    Cmd("exit 0", stack).run()


def test_nonzero_exit_raises_exception(stack):
    with pytest.raises(CalledProcessError):
        Cmd("exit 1", stack).run()


def test_command_writes_to_stdout(stack, capfd):
    Cmd("echo hello", stack).run()
    cap = capfd.readouterr()
    assert cap.out.strip() == "hello"
    assert cap.err.strip() == ""


def test_shell_error_writes_to_stderr(stack, capfd):
    try:
        Cmd("missing_command", stack).run()
    except CalledProcessError:
        cap = capfd.readouterr()
        assert cap.out.strip() == ""
        assert "missing_command: not found" in cap.err


def test_default_shell_is_sh(stack, capfd):
    Cmd("echo $0", stack).run()
    cap = capfd.readouterr()
    assert cap.out.strip() == "/bin/sh"
    assert cap.err.strip() == ""


def test_executable_sets_the_shell(stack, capfd):
    Cmd({"args": "echo $0", "executable": "/bin/bash"}, stack).run()
    cap = capfd.readouterr()
    assert cap.out.strip() == "/bin/bash"
    assert cap.err.strip() == ""


def test_shell_has_session_environment_variables(stack, capfd):
    stack.connection_manager.create_session_environment_variables = Mock(
        return_value={"AWS_PROFILE": "sceptre_profile"}
    )
    Cmd("env | grep -E '^AWS_PROFILE='", stack).run()
    cap = capfd.readouterr()
    assert cap.out.strip() == "AWS_PROFILE=sceptre_profile"
    assert cap.err.strip() == ""
