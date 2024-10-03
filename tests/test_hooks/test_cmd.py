# -*- coding: utf-8 -*-
from subprocess import CalledProcessError
from unittest.mock import Mock
import pytest

from sceptre.exceptions import InvalidHookArgumentTypeError
from sceptre.hooks.cmd import Cmd
from sceptre.stack import Stack

ERROR_MESSAGE = (
    r"^A cmd hook requires either a string argument or an object with `run` and "
    r"`shell` keys with string values\. You gave `{0}`\.$"
)


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
    message = ERROR_MESSAGE.format(r"None")
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd(None, stack).run()


def test_empty_string_raises_exception(stack):
    message = ERROR_MESSAGE.format(r"''")
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd("", stack).run()


def test_list_raises_exception(stack):
    message = ERROR_MESSAGE.format(r"\['echo', 'hello'\]")
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd(["echo", "hello"], stack).run()


def test_dict_without_shell_raises_exception(stack):
    message = ERROR_MESSAGE.format(r"\{'run': 'echo hello'\}")
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd({"run": "echo hello"}, stack).run()


def test_dict_without_run_raises_exception(stack):
    message = ERROR_MESSAGE.format(r"\{'shell': '/bin/bash'\}")
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd({"shell": "/bin/bash"}, stack).run()


def test_dict_with_list_run_raises_exception(stack):
    message = ERROR_MESSAGE.format(
        r"\{'run': \['echo', 'hello'\], 'shell': '/bin/bash'\}"
    )
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd({"run": ["echo", "hello"], "shell": "/bin/bash"}, stack).run()


def test_dict_with_empty_run_raises_exception(stack):
    message = ERROR_MESSAGE.format(r"\{'run': '', 'shell': '/bin/bash'\}")
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd({"run": "", "shell": "/bin/bash"}, stack).run()


def test_dict_with_null_run_raises_exception(stack):
    message = ERROR_MESSAGE.format(r"\{'run': None, 'shell': '/bin/bash'\}")
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd({"run": None, "shell": "/bin/bash"}, stack).run()


def test_dict_with_list_shell_raises_exception(stack):
    message = ERROR_MESSAGE.format(r"\{'run': 'echo hello', 'shell': \['/bin/bash'\]\}")
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd({"run": "echo hello", "shell": ["/bin/bash"]}, stack).run()


def test_dict_with_typo_shell_raises_exception(stack):
    message = r"^\[Errno 2\] No such file or directory: '/bin/bsah'$"
    with pytest.raises(FileNotFoundError, match=message):
        typo = "/bin/bsah"
        Cmd({"run": "echo hello", "shell": typo}, stack).run()


def test_dict_with_non_executable_shell_raises_exception(stack):
    message = r"^\[Errno 13\] Permission denied: '/'$"
    with pytest.raises(PermissionError, match=message):
        Cmd({"run": "echo hello", "shell": "/"}, stack).run()


def test_dict_with_empty_shell_raises_exception(stack):
    message = ERROR_MESSAGE.format(r"\{'run': 'echo hello', 'shell': ''\}")
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd({"run": "echo hello", "shell": ""}, stack).run()


def test_dict_with_null_shell_raises_exception(stack):
    message = ERROR_MESSAGE.format(r"\{'run': 'echo hello', 'shell': None\}")
    with pytest.raises(InvalidHookArgumentTypeError, match=message):
        Cmd({"run": "echo hello", "shell": None}, stack).run()


def test_input_exception_reprs_input(stack):
    import datetime

    exception_message = ERROR_MESSAGE.format(r"datetime.date\(2023, 8, 31\)")
    with pytest.raises(InvalidHookArgumentTypeError, match=exception_message):
        Cmd(datetime.date(2023, 8, 31), stack).run()


def test_zero_exit_returns(stack):
    Cmd("exit 0", stack).run()


def test_nonzero_exit_raises_exception(stack):
    message = r"Command 'exit 1' returned non-zero exit status 1\."
    with pytest.raises(CalledProcessError, match=message):
        Cmd("exit 1", stack).run()


def test_hook_writes_to_stdout(stack, capfd):
    Cmd("echo hello", stack).run()
    cap = capfd.readouterr()
    assert cap.out.strip() == "hello"
    assert cap.err.strip() == ""


def test_hook_writes_to_stderr(stack, capfd):
    Cmd("echo hello >&2", stack).run()
    cap = capfd.readouterr()
    assert cap.out.strip() == ""
    assert cap.err.strip() == "hello"


def test_default_shell_is_sh(stack, capfd):
    Cmd("echo $0", stack).run()
    cap = capfd.readouterr()
    assert cap.out.strip().split("/")[-2:] == ["bin", "sh"]
    assert cap.err.strip() == ""


def test_shell_parameter_sets_the_shell(stack, capfd):
    # Determine the local path to bash (it's not always /bin/bash)
    Cmd("echo $0", stack).run()
    cap = capfd.readouterr()
    assert cap.err.strip() == ""
    bash = cap.out.strip()

    # Confirm the correct shell is used in the sub-process
    Cmd({"run": "echo $0", "shell": bash}, stack).run()
    cap = capfd.readouterr()
    assert cap.out.strip() == bash
    assert cap.err.strip() == ""


def test_shell_has_session_environment_variables(stack, capfd):
    stack.connection_manager.create_session_environment_variables = Mock(
        return_value={"AWS_PROFILE": "sceptre_profile"}
    )
    Cmd("echo $AWS_PROFILE", stack).run()
    cap = capfd.readouterr()
    assert cap.out.strip() == "sceptre_profile"
    assert cap.err.strip() == ""
