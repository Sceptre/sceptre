import logging
import pathlib
import os
import sys
import tempfile
import traceback

from importlib.machinery import SourceFileLoader
from jinja2 import Environment, select_autoescape, FileSystemLoader, StrictUndefined

from sceptre.exceptions import UnsupportedTemplateFileTypeError, TemplateSceptreHandlerError
from sceptre.template_handlers import TemplateHandler

logger = logging.getLogger(__name__)


class S3(TemplateHandler):
    """
    Template handler that can resolve templates from S3.  Raw CFN templates
    with extension (.json, .yaml, .template) are deployed directly from memory
    while references to jinja (.j2) and python (.py) templates are downloaded,
    transformed into CFN templates then deployed to AWS.
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        super(S3, self).__init__(*args, **kwargs)

    def schema(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }

    def handle(self):
        """
        handle template in S3 bucket
        """
        input_path = self.arguments["path"]
        path = pathlib.Path(input_path)
        bucket = path.parts[0]
        key = "/".join(path.parts[1:])

        raw_template_suffix = [".json", ".yaml", ".template"]
        jinja_template_suffix = [".j2"]
        python_template_suffix = [".py"]
        supported_suffix = raw_template_suffix + jinja_template_suffix + python_template_suffix

        if path.suffix not in supported_suffix:
            raise UnsupportedTemplateFileTypeError(
                "Template has file extension %s. Only .py, .yaml, "
                ".template, .json and .j2 are supported.",
                path.suffix
            )

        try:
            template = self._get_template(bucket, key)
            if path.suffix in jinja_template_suffix + python_template_suffix:
                file = tempfile.NamedTemporaryFile(prefix=path.stem)
                with file as f:
                    f.write(template)
                    f.seek(0)
                    f.read()
                    if path.suffix in jinja_template_suffix:
                        template = self._render_jinja_template(
                            os.path.dirname(f.name),
                            os.path.basename(f.name),
                            {"sceptre_user_data": self.sceptre_user_data}
                        )
                    elif path.suffix in python_template_suffix:
                        template = self._call_sceptre_handler(f.name)

        except Exception as e:
            self._print_template_traceback()
            raise e

        return template

    def _get_template(self, bucket, key):
        """
        Get template from S3 bucket

        :returns: The body of the CloudFormation template.
        :rtype: str
        """
        self.logger.debug("Downloading file from S3: %s" % self.arguments["path"])

        try:
            response = self.connection_manager.call(
                service="s3",
                command="get_object",
                kwargs={
                    "Bucket": bucket,
                    "Key": key
                }
            )
            return response["Body"].read()
        except Exception as e:
            self.logger.fatal(e)
            raise e

    def _call_sceptre_handler(self, path):
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
        # path = self.arguments["path"]

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

        module = SourceFileLoader(path, path).load_module()

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
