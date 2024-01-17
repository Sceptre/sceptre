"""
This module contains a template handler that can load files from disk and
format the content.
"""
import re
import os
from sceptre.template_handlers.file import File


class FormattedYaml(File):
    """
    Template handler that can load files from disk.
    Supports JSON, YAML, Jinja2 and Python.

    This class extends the `File` class from the
    `sceptre.template_handlers.file` module. It provides additional
    functionality to format YAML content by removing trailing whitespaces
    and blank lines, adding line breaks before lines that don't start with
    spaces, tabs, or specific prefixes, and adding a newline at the end
    of the file.
    """

    # Class attribute for line start exceptions
    no_newline_prefixes = ["---", "AWSTemplateFormatVersion", "Description"]

    def handle(self):
        """
        Handles the template by returning the template contents.

        Returns:
            str or bytes: The template contents.
        """
        contents = super().handle()
        if isinstance(contents, str):
            return self._format_yaml_content(contents)
        return contents

    def _format_yaml_content(self, input_string: str) -> str:
        """
        Formats the input string by removing trailing whitespaces
        and blank lines, adding a line break before every line that
        doesn't start with spaces, tabs, or specific prefixes, and adding
        a newline at the end of the file.

        Args:
            input_string (str): The input string that needs to be formatted.

        Returns:
            str: The formatted string.
        """
        # Remove trailing whitespaces and blank lines
        result = re.sub(r"^\s*\n", "", input_string, flags=re.MULTILINE)
        result = re.sub(r"\s+$", "", result, flags=re.MULTILINE)

        # Construct the pattern for line start exceptions
        exceptions_pattern = "|".join(
            re.escape(prefix) for prefix in self.no_newline_prefixes
        )  # noqa: E501  pylint: disable=line-too-long
        pattern = r"^(?!" + exceptions_pattern + r")([^\s\t].*)$"

        # Add a line break before every line that doesn't start with
        # spaces, tabs, or specific prefixes
        result = re.sub(pattern, r"\n\1", result, flags=re.MULTILINE)

        # Add a newline at the end of the file
        result = result + os.linesep

        return result
