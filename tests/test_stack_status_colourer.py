# -*- coding: utf-8 -*-

from colorama import init, Fore, Style
from sceptre.stack_status_colourer import StackStatusColourer


class TestStackStatusColourer(object):

    def setup_method(self, test_method):
        init()
        self.stack_status_colourer = StackStatusColourer()
        self.statuses = {
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

    def test_colour_with_string_with_no_stack_statuses(self):
        response = self.stack_status_colourer.colour("string with no statuses")
        assert response == "string with no statuses"

    def test_colour_with_string_with_single_stack_status(self):
        strings = [
            "string string {0} string".format(status)
            for status in sorted(self.statuses.keys())
        ]

        responses = [
            self.stack_status_colourer.colour(string)
            for string in strings
        ]

        assert responses == [
            "string string {0}{1}{2} string".format(
                self.statuses[status],
                status,
                Style.RESET_ALL
            )
            for status in sorted(self.statuses.keys())
        ]

    def test_colour_with_string_with_multiple_stack_statuses(self):
        response = self.stack_status_colourer.colour(
            " ".join(sorted(self.statuses.keys()))
        )
        assert response == " ".join([
            "{0}{1}{2}".format(
                self.statuses[status],
                status,
                Style.RESET_ALL
            )
            for status in sorted(self.statuses.keys())
        ])
