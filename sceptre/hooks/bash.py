import subprocess
from sceptre.hooks import Hook
from sceptre.exceptions import InvalidHookArgumentTypeError


class Bash(Hook):
    """
    This command with execute the argument string with bash.

    """
    ALLOW_COMMAND_ERROR = True

    def __init__(self, *args, **kwargs):
        super(Bash, self).__init__(*args, **kwargs)

    def run(self):
        """
        Runs argument string in child process with bash.

        :raise: sceptre.exceptions.InvalidTaskArgumentTypeException
        """
        if not isinstance(self.argument, basestring):
            raise InvalidHookArgumentTypeError(
                'The argument "{0}" is the wrong type - Bash hooks require '
                'arguments of type string.'.format(self.argument)
            )

        if Bash.ALLOW_COMMAND_ERROR:
            subprocess.call(["/bin/bash", "-c", self.argument])
        else:
            subprocess.check_call(["/bin/bash", "-c", self.argument])
