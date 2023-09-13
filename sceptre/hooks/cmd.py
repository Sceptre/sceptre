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

        if isinstance(self.argument, str) and self.argument != "":
            command_to_run = self.argument
            shell = None

        elif (
            isinstance(self.argument, dict)
            and set(self.argument) == {"run", "shell"}
            and isinstance(self.argument["run"], str)
            and isinstance(self.argument["shell"], str)
            and self.argument["run"] != ""
            and self.argument["shell"] != ""
        ):
            command_to_run = self.argument["run"]
            shell = self.argument["shell"]

        else:
            raise InvalidHookArgumentTypeError(
                "A cmd hook requires either a string argument or an object with "
                "`run` and `shell` keys with string values. "
                f"You gave `{self.argument!r}`."
            )

        subprocess.check_call(command_to_run, shell=True, env=envs, executable=shell)
