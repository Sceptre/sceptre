import os
import sceptre.template_handlers.helper as helper

from pathlib import Path
from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers import TemplateHandler


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
            "required": ["path"]
        }

    def handle(self):
        project_path = self.stack_group_config.get("project_path")
        input_path = Path(self.arguments["path"])
        if input_path.is_absolute():
            path = str(input_path)
        else:
            path = str(Path(project_path) / 'templates' / input_path)

        if input_path.suffix not in self.supported_template_extensions:
            raise UnsupportedTemplateFileTypeError(
                "Template has file extension %s. Only %s are supported.",
                input_path.suffix, ",".join(self.supported_template_extensions)
            )

        try:
            if input_path.suffix in self.standard_template_extensions:
                with open(path) as template_file:
                    return template_file.read()
            elif input_path.suffix in self.jinja_template_extensions:
                return helper.render_jinja_template(
                    os.path.dirname(path),
                    os.path.basename(path),
                    {"sceptre_user_data": self.sceptre_user_data},
                    self.stack_group_config.get("j2_environment", {})
                )
            elif input_path.suffix in self.python_template_extensions:
                return helper.call_sceptre_handler(path,
                                                   self.sceptre_user_data)
        except Exception as e:
            helper.print_template_traceback(path)
            raise e
