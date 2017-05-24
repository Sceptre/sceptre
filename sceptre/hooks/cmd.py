import subprocess
from sceptre.hooks import Hook
from sceptre.exceptions import InvalidHookArgumentTypeError


class Cmd(Hook):
    """
    Cmd implements a Sceptre hook which can run arbitrary shell commands.
    """

    def __init__(self, *args, **kwargs):
        super(Cmd, self).__init__(*args, **kwargs)

    def run(self):
        """
        Runs the argument string in child process.

        :raises: sceptre.exceptions.InvalidTaskArgumentTypeException
        :raises: subprocess.CalledProcessError
        """
        if not isinstance(self.argument, basestring):
            raise InvalidHookArgumentTypeError(
                'The argument "{0}" is the wrong type - cmd hooks require '
                'arguments of type string.'.format(self.argument)
            )
        subprocess.check_call(["/bin/bash", "-c", self.argument])
