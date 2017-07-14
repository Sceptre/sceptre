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
        try:
            subprocess.check_call(self.argument, shell=True)
        except TypeError:
            raise InvalidHookArgumentTypeError(
                'The argument "{0}" is the wrong type - cmd hooks require '
                'arguments of type string.'.format(self.argument)
            )
