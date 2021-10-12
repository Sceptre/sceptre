import logging
import pathlib
import os
import requests
import tempfile
import sceptre.template_handlers.helper as helper

from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers import TemplateHandler
from urllib.parse import urlparse


class Web(TemplateHandler):
    """
    Template handler that can resolve templates from the web.  Raw CFN templates
    with extension (.json, .yaml, .template) are deployed directly from memory
    while references to jinja (.j2) and python (.py) templates are downloaded,
    transformed into CFN templates then deployed to AWS.
    """
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        super(Web, self).__init__(*args, **kwargs)

    def schema(self):
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string"}
            },
            "required": ["url"]
        }

    def handle(self):
        """
        handle template from web
        """
        url = self.arguments["url"]
        path = pathlib.Path(urlparse(url).path)

        standard_template_suffix = [".json", ".yaml", ".template"]
        jinja_template_suffix = [".j2"]
        python_template_suffix = [".py"]
        supported_suffix = standard_template_suffix + jinja_template_suffix + python_template_suffix

        if path.suffix not in supported_suffix:
            raise UnsupportedTemplateFileTypeError(
                "Template has file extension %s. Only %s are supported.",
                path.suffix, ",".join(supported_suffix)
            )

        try:
            template = self._get_template(url)
            if path.suffix in jinja_template_suffix + python_template_suffix:
                file = tempfile.NamedTemporaryFile(prefix=path.stem)
                with file as f:
                    f.write(template)
                    f.seek(0)
                    f.read()
                    if path.suffix in jinja_template_suffix:
                        template = helper.render_jinja_template(
                            os.path.dirname(f.name),
                            os.path.basename(f.name),
                            {"sceptre_user_data": self.sceptre_user_data}
                        )
                    elif path.suffix in python_template_suffix:
                        template = helper.call_sceptre_handler(
                            f.name,
                            self.sceptre_user_data
                        )

        except Exception as e:
            helper.print_template_traceback(path)
            raise e

        return template

    def _get_template(self, url):
        """
        Get template from the web
        :param url: The url to the template
        :type: str
        :returns: The body of the CloudFormation template.
        :rtype: str
        """
        self.logger.debug("Downloading file from web: %s", url)
        try:
            response = requests.get(url)
            return response.content
        except requests.exceptions.RequestException as e:
            self.logger.fatal(e)
            raise e
