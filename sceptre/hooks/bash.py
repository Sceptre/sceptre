import subprocess
import warnings
from six import string_types

from colorama import Fore, Style

from sceptre.hooks import Hook
from sceptre.exceptions import InvalidHookArgumentTypeError


class Bash(Hook):
    """
    This hook has been deprecated in favor of cmd hook.
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
        warnings.warn(
            "{0}The bash hook has been deprecated, and will "
            "be removed in a later version of Sceptre. "
            "Use the cmd hook instead. Example: !cmd <command>{1}"
            .format(Fore.YELLOW, Style.RESET_ALL),
            DeprecationWarning
        )
        if not isinstance(self.argument, string_types):
            raise InvalidHookArgumentTypeError(
                'The argument "{0}" is the wrong type - Bash hooks require '
                'arguments of type string.'.format(self.argument)
            )

        if Bash.ALLOW_COMMAND_ERROR:
            subprocess.call(["/bin/bash", "-c", self.argument])
        else:
            subprocess.check_call(["/bin/bash", "-c", self.argument])
