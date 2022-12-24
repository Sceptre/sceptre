# -*- coding: utf-8 -*-
import sceptre.template_handlers.helper as helper

from os import path
from pathlib import Path

from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers import TemplateHandler
from sceptre.helpers import normalise_path


class File(TemplateHandler):
    """
    Template handler that can load files from disk. Supports JSON, YAML, Jinja2 and Python.
    """

    def __init__(self, *args, **kwargs):
        super(File, self).__init__(*args, **kwargs)

    def schema(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
        }

    def handle(self):
        input_path = Path(self.arguments["path"])
        path = self._resolve_template_path(str(input_path))

        if input_path.suffix not in self.supported_template_extensions:
            raise UnsupportedTemplateFileTypeError(
                "Template has file extension %s. Only %s are supported.",
                input_path.suffix,
                ",".join(self.supported_template_extensions),
            )

        try:
            if input_path.suffix in self.standard_template_extensions:
                with open(path) as template_file:
                    return template_file.read()
            elif input_path.suffix in self.jinja_template_extensions:
                return helper.render_jinja_template(
                    path,
                    {"sceptre_user_data": self.sceptre_user_data},
                    self.stack_group_config.get("j2_environment", {}),
                )
            elif input_path.suffix in self.python_template_extensions:
                return helper.call_sceptre_handler(path, self.sceptre_user_data)
        except Exception as e:
            helper.print_template_traceback(path)
            raise e

    def _resolve_template_path(self, template_path):
        """
        Return the project_path joined to template_path as
        a string.

        Note that os.path.join defers to an absolute path
        if the input is absolute.
        """
        return path.join(
            self.stack_group_config["project_path"],
            "templates",
            normalise_path(template_path),
        )
