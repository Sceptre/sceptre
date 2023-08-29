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
        Runs the argument string in a subprocess.

        :raises: sceptre.exceptions.InvalidTaskArgumentTypeException
        :raises: subprocess.CalledProcessError
        """
        envs = self.stack.connection_manager.create_session_environment_variables()

        if self.argument is None:
            raise InvalidHookArgumentTypeError()

        if isinstance(self.argument, str) or self.argument is None:
            args = self.argument
            executable = None
        elif isinstance(self.argument, dict):
            args = self.argument["args"]
            executable = self.argument["executable"]

        subprocess.check_call(args, shell=True, env=envs, executable=executable)
