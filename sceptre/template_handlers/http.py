# -*- coding: utf-8 -*-
import pathlib
import tempfile
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import sceptre.template_handlers.helper as helper
from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers import TemplateHandler

HANDLER_OPTION_KEY = "http_template_handler"
HANDLER_RETRIES_OPTION_PARAM = "retries"
DEFAULT_RETRIES_OPTION = 5
HANDLER_TIMEOUT_OPTION_PARAM = "timeout"
DEFAULT_TIMEOUT_OPTION = 5


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
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
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
                path.suffix,
                ",".join(self.supported_template_extensions),
            )

        retries = self._get_handler_option(
            HANDLER_RETRIES_OPTION_PARAM, DEFAULT_RETRIES_OPTION
        )
        timeout = self._get_handler_option(
            HANDLER_TIMEOUT_OPTION_PARAM, DEFAULT_TIMEOUT_OPTION
        )
        try:
            template = self._get_template(url, retries=retries, timeout=timeout)
            if (
                path.suffix
                in self.jinja_template_extensions + self.python_template_extensions
            ):
                file = tempfile.NamedTemporaryFile(prefix=path.stem)
                self.logger.debug("Template file saved to: %s", file.name)
                with file as f:
                    f.write(template)
                    f.seek(0)
                    f.read()
                    if path.suffix in self.jinja_template_extensions:
                        template = helper.render_jinja_template(
                            f.name,
                            {"sceptre_user_data": self.sceptre_user_data},
                            self.stack_group_config.get("j2_environment", {}),
                        )
                    elif path.suffix in self.python_template_extensions:
                        template = helper.call_sceptre_handler(
                            f.name, self.sceptre_user_data
                        )

        except Exception as e:
            helper.print_template_traceback(path)
            raise e

        return template

    def _get_template(self, url: str, retries: int, timeout: int) -> str:
        """
        Get template from the web
        :param url: The url to the template
        :param retries: The number of retry attempts.
        :param timeout: The timeout for the session in seconds.
        :raises: :class:`requests.exceptions.HTTPError`: When a download error occurs
        """
        self.logger.debug("Downloading file from: %s", url)
        session = self._get_retry_session(retries=retries)
        response = session.get(url, timeout=timeout)

        # If the response was unsuccessful, raise an error.
        response.raise_for_status()

        return response.content

    def _get_retry_session(
        self,
        retries,
        backoff_factor=0.3,
        status_forcelist=(429, 500, 502, 503, 504),
        session=None,
    ):
        """
        Get a request session with retries.  Retry options are explained in the request libraries
        https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#module-urllib3.util.retry
        """
        session = session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_handler_option(self, name, default):
        """
        Get the template handler options
        :param url: The option name
        :type: str
        :param default: The default value if option is not set.
        :rtype: int
        """
        if HANDLER_OPTION_KEY in self.stack_group_config:
            option = self.stack_group_config.get(HANDLER_OPTION_KEY)
            if name in option:
                return option.get(name)

        return default
