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

        :raises: sceptre.exceptions.InvalidHookArgumentTypeError
        :raises: subprocess.CalledProcessError
        """
        envs = self.stack.connection_manager.create_session_environment_variables()

        if isinstance(self.argument, str) and self.argument != "":
            command = self.argument
            shell = None

        elif (
            isinstance(self.argument, dict)
            and set(self.argument) == {"command", "shell"}
            and isinstance(self.argument["command"], str)
            and isinstance(self.argument["shell"], str)
        ):
            command = self.argument["command"]
            shell = self.argument["shell"]

        else:
            raise InvalidHookArgumentTypeError(
                "A cmd hook requires either a string argument or an object with "
                "`command` and `shell` keys with string values. "
                f"You gave `{self.argument!r}`."
            )

        subprocess.check_call(command, shell=True, env=envs, executable=shell)
