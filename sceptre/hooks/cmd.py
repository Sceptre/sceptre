import subprocess
from sceptre.hooks import Hook
from sceptre.exceptions import InvalidHookArgumentTypeError


class Cmd(Hook):
    """
    Cmd implements a Sceptre hook which can run arbitrary commands.
    """

    def __init__(self, *args, **kwargs):
        super(Cmd, self).__init__(*args, **kwargs)

    def run(self):
        """
        Executes a command through the shell.

        See hooks documentation for details.

        :raises: sceptre.exceptions.InvalidHookArgumentTypeError invalid input
        :raises: CalledProcessError failed command
        :raises: FileNotFoundError missing shell
        :raises: PermissionError non-executable shell
        """
        envs = self.stack.connection_manager.create_session_environment_variables()

        command_to_run = None
        shell = None

        if isinstance(self.argument, dict):
            command_to_run = self.argument.get("run")
            shell = self.argument.get("shell")
        else:
            command_to_run = self.argument

        if not isinstance(command_to_run, str) or command_to_run == "":
            raise InvalidHookArgumentTypeError(
                "A cmd hook requires either a string argument or an object with "
                f"a `run` key and a string value. You gave `{self.argument!r}`."
            )

        if shell is not None and not isinstance(shell, str) or shell == "":
            raise InvalidHookArgumentTypeError(
                "A cmd hook requires a `shell` key with a non-empty string. "
                f"You gave `{self.argument!r}`."
            )

        subprocess.check_call(command_to_run, shell=True, env=envs, executable=shell)
