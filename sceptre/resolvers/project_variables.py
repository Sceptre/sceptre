# -*- coding: utf-8 -*-

import os
import yaml
import warnings

from colorama import Fore, Style

from sceptre.resolvers import Resolver


class ProjectVariables(Resolver):
    """
    Resolver for the configuration in a file.

    :param argument: Configuration value to be returned.
    :type argument: str
    """

    def __init__(self, *args, **kwargs):
        super(ProjectVariables, self).__init__(*args, **kwargs)

    def resolve(self):
        """
        Searches for value at given key location.

        :returns: Value at argument location.
        :rtype: str
        """
        warnings.warn(
            "{0}The project_variables resolver has been deprecated, and will "
            "be removed in a later version of Sceptre. Depending on your "
            "use case, you may find user variables appropiate. "
            "Example: sceptre --var \"iam_role=<your iam role>\" <COMMAND>{1}"
            .format(Fore.YELLOW, Style.RESET_ALL),
            DeprecationWarning
        )
        file_path = os.path.join(
            self.environment_config.sceptre_dir,
            self.argument
        )

        with open(file_path, "r") as f:
            variables_dict = yaml.safe_load(f)

        dict_keys = self.environment_config.environment_path.split("/")
        dict_keys.append(self.stack_config.name)

        for key in dict_keys:
            variables_dict = variables_dict[key]

        return variables_dict
