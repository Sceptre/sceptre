# -*- coding: utf-8 -*-

import os

from sceptre.resolvers import Resolver


class EnvironmentVariable(Resolver):
    """
    Resolver for shell environment variables.

    :param argument: Name of the environment variable to return.
    :type argument: str
    """

    def __init__(self, *args, **kwargs):
        super(EnvironmentVariable, self).__init__(*args, **kwargs)

    def resolve(self):
        """
        Retrieves the value of a named environment variable.

        :returns: Value of the environment variable.
        :rtype: str
        """
        return os.environ.get(None if self.argument == {} else self.argument)
