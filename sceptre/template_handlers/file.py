import logging
import os

from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers.helper import Helper
from sceptre.template_handlers import TemplateHandler


class File(TemplateHandler):
    """
    Template handler that can load files from disk. Supports JSON, YAML, Jinja2 and Python.
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        super(File, self).__init__(*args, **kwargs)

    def schema(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"]
        }

    def handle(self):
        file_extension = os.path.splitext(self.arguments["path"])[1]
        path = self.arguments["path"]
        try:
            if file_extension in {".json", ".yaml", ".template"}:
                with open(path) as template_file:
                    return template_file.read()
            elif file_extension == ".j2":
                return Helper.render_jinja_template(
                    os.path.dirname(path),
                    os.path.basename(path),
                    {"sceptre_user_data": self.sceptre_user_data}
                )
            elif file_extension == ".py":
                return Helper.call_sceptre_handler(path,
                                                   self.sceptre_user_data)
            else:
                raise UnsupportedTemplateFileTypeError(
                    "Template has file extension %s. Only .py, .yaml, "
                    ".template, .json and .j2 are supported.",
                    os.path.splitext(path)[1]
                )
        except Exception as e:
            Helper.print_template_traceback(path)
            raise e
