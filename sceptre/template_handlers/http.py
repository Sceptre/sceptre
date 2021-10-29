# -*- coding: utf-8 -*-
import pathlib
import requests
import tempfile
import sceptre.template_handlers.helper as helper

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers import TemplateHandler
from urllib.parse import urlparse


class Http(TemplateHandler):
    """
    Template handler that can resolve templates from the web.  Standard CFN templates
    with extension (.json, .yaml, .template) are deployed directly from memory
    while references to jinja (.j2) and python (.py) templates are downloaded,
    transformed into CFN templates then deployed to AWS.
    """
    def __init__(self, *args, **kwargs):
        super(Http, self).__init__(*args, **kwargs)

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

        if path.suffix not in self.supported_template_extensions:
            raise UnsupportedTemplateFileTypeError(
                "Template has file extension %s. Only %s are supported.",
                path.suffix, ",".join(self.supported_template_extensions)
            )

        try:
            template = self._get_template(url)
            if path.suffix in self.jinja_template_extensions + self.python_template_extensions:
                file = tempfile.NamedTemporaryFile(prefix=path.stem)
                self.logger.debug("Template file saved to: %s", file.name)
                with file as f:
                    f.write(template)
                    f.seek(0)
                    f.read()
                    if path.suffix in self.jinja_template_extensions:
                        template = helper.render_jinja_template(f.name,
                                                                {"sceptre_user_data": self.sceptre_user_data},
                                                                self.stack_group_config.get("j2_environment", {}))
                    elif path.suffix in self.python_template_extensions:
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
        self.logger.debug("Downloading file from: %s", url)
        session = self._get_retry_session(session=requests.Session())
        try:
            response = session.get(url, timeout=(2, 5))
            return response.content
        except Exception as e:
            self.logger.fatal(e)
            raise e

    def _get_retry_session(self,
                           retries=5,
                           backoff_factor=0.3,
                           status_forcelist=(429, 500, 502, 503, 504),
                           session=None):
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
