# -*- coding: utf-8 -*-

"""
sceptre.stack_status_colourer

This module implements a StackStatusColourer class, colours any Stack Statuses
found in a given string.
"""

import re
from colorama import Fore, Style


class StackStatusColourer(object):
    """
    StackStatusColourer adds colours to stack statuses.
    """

    STACK_STATUS_CODES = {
        "PENDING": Fore.CYAN,
        "CREATE_COMPLETE": Fore.GREEN,
        "CREATE_FAILED": Fore.RED,
        "CREATE_IN_PROGRESS": Fore.YELLOW,
        "DELETE_COMPLETE": Fore.GREEN,
        "DELETE_FAILED": Fore.RED,
        "DELETE_IN_PROGRESS": Fore.YELLOW,
        "ROLLBACK_COMPLETE": Fore.RED,
        "ROLLBACK_FAILED": Fore.RED,
        "ROLLBACK_IN_PROGRESS": Fore.YELLOW,
        "UPDATE_COMPLETE": Fore.GREEN,
        "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS": Fore.YELLOW,
        "UPDATE_FAILED": Fore.RED,
        "UPDATE_IN_PROGRESS": Fore.YELLOW,
        "UPDATE_ROLLBACK_COMPLETE": Fore.GREEN,
        "UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS": Fore.YELLOW,
        "UPDATE_ROLLBACK_FAILED": Fore.RED,
        "UPDATE_ROLLBACK_IN_PROGRESS": Fore.YELLOW
    }

    STACK_STATUS_PATTERN = re.compile(
        r"\b({0})\b".format("|".join(STACK_STATUS_CODES))
    )

    def colour(self, string):
        """
        Colours all Stack Statueses in ``string``.

        The colours applied are defined in
        ``sceptre.stack_status_colourer.StackStatusColourer.STACK_STATUS_CODES``

        :param string: A string to colour.
        :type string: str
        :returns: The string with all stack status values coloured.
        :rtype: str
        """
        stack_statuses = re.findall(self.STACK_STATUS_PATTERN, string)
        for status in stack_statuses:
            string = re.sub(
                r"\b{0}\b".format(status),
                "{0}{1}{2}".format(
                    self.STACK_STATUS_CODES[status], status, Style.RESET_ALL
                ),
                string
            )
        return string
