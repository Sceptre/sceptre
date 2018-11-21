from __future__ import print_function

from sceptre.hooks import Hook


class CustomHook(Hook):
    """
    This is a test task.

    """
    def __init__(self, *args, **kwargs):
        super(CustomHook, self).__init__(*args, **kwargs)

    def run(self):
        """
        Prints a statement

        """
        print("Custom task output")
