import logging
import os
import sys
import traceback

from jinja2 import Environment, select_autoescape, FileSystemLoader, StrictUndefined

from sceptre.exceptions import UnsupportedTemplateFileTypeError, TemplateSceptreHandlerError
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
                return self._render_jinja_template(
                    os.path.dirname(path),
                    os.path.basename(path),
                    {"sceptre_user_data": self.sceptre_user_data}
                )
            elif file_extension == ".py":
                return self._call_sceptre_handler()
            else:
                raise UnsupportedTemplateFileTypeError(
                    "Template has file extension %s. Only .py, .yaml, "
                    ".template, .json and .j2 are supported.",
                    os.path.splitext(path)[1]
                )
        except Exception as e:
            self._print_template_traceback()
            raise e

    def _call_sceptre_handler(self):
        """
        Calls the function `sceptre_handler` within templates that are python
        scripts.

        :returns: The string returned from sceptre_handler in the template.
        :rtype: str
        :raises: IOError
        :raises: TemplateSceptreHandlerError
        """
        # Get relative path as list between current working directory and where
        # the template is
        # NB: this is a horrible hack...
        path = self.arguments["path"]

        relpath = os.path.relpath(path, os.getcwd()).split(os.path.sep)
        relpaths_to_add = [
            os.path.sep.join(relpath[:i + 1])
            for i in range(len(relpath[:-1]))
        ]
        # Add any directory between the current working directory and where
        # the template is to the python path
        for directory in relpaths_to_add:
            sys.path.append(os.path.join(os.getcwd(), directory))
        self.logger.debug(
            "%s - Getting CloudFormation from %s", self.name, path
        )

        if not os.path.isfile(path):
            raise IOError("No such file or directory: '%s'", path)

        import imp
        module = imp.load_source(self.name, path)

        try:
            body = module.sceptre_handler(self.sceptre_user_data)
        except AttributeError as e:
            if 'sceptre_handler' in str(e):
                raise TemplateSceptreHandlerError(
                    "The template does not have the required "
                    "'sceptre_handler(sceptre_user_data)' function."
                )
            else:
                raise e
        for directory in relpaths_to_add:
            sys.path.remove(os.path.join(os.getcwd(), directory))
        return body

    def _print_template_traceback(self):
        """
        Prints a stack trace, including only files which are inside a
        'templates' directory. The function is intended to give the operator
        instant feedback about why their templates are failing to compile.

        :rtype: None
        """

        def _print_frame(filename, line, fcn, line_text):
            self.logger.error("{}:{}:  Template error in '{}'\n=> `{}`".format(
                filename, line, fcn, line_text))

        try:
            _, _, tb = sys.exc_info()
            stack_trace = traceback.extract_tb(tb)
            search_string = os.path.join('', 'templates', '')
            if search_string in self.arguments["path"]:
                template_path = self.arguments["path"].split(search_string)[0] + search_string
            else:
                return
            for frame in stack_trace:
                if isinstance(frame, tuple):
                    # Python 2 / Old style stack frame
                    if template_path in frame[0]:
                        _print_frame(frame[0], frame[1], frame[2], frame[3])
                else:
                    if template_path in frame.filename:
                        _print_frame(frame.filename, frame.lineno, frame.name, frame.line)
        except Exception as tb_exception:
            self.logger.error(
                'A template error occured. ' +
                'Additionally, a traceback exception occured. Exception: %s',
                tb_exception
            )

    @staticmethod
    def _render_jinja_template(template_dir, filename, jinja_vars):
        """
        Renders a jinja template.

        Sceptre supports passing sceptre_user_data to JSON and YAML
        CloudFormation templates using Jinja2 templating.

        :param template_dir: The directory containing the template.
        :type template_dir: str
        :param filename: The name of the template file.
        :type filename: str
        :param jinja_vars: Dict of variables to render into the template.
        :type jinja_vars: dict
        :returns: The body of the CloudFormation template.
        :rtype: str
        """
        logger = logging.getLogger(__name__)
        logger.debug("%s Rendering CloudFormation template", filename)
        env = Environment(
            autoescape=select_autoescape(
                disabled_extensions=('j2',),
                default=True,
            ),
            loader=FileSystemLoader(template_dir),
            undefined=StrictUndefined
        )
        template = env.get_template(filename)
        body = template.render(**jinja_vars)
        return body
