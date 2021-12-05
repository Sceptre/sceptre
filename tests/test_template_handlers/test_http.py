# -*- coding: utf-8 -*-
import json

import pytest

from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers.http import Http
from unittest.mock import patch


class TestHttp(object):

    def test_get_template(self, requests_mock):
        url = "https://raw.githubusercontent.com/acme/bucket.yaml"
        requests_mock.get(url, content=b"Stuff is working")
        template_handler = Http(
            name="vpc",
            arguments={"url": url},
        )
        result = template_handler.handle()
        assert result == b"Stuff is working"

    def test_handler_unsupported_type(self):
        handler = Http("http_handler", {'url': 'https://raw.githubusercontent.com/acme/bucket.unsupported'})
        with pytest.raises(UnsupportedTemplateFileTypeError):
            handler.handle()

    @pytest.mark.parametrize("url", [
        ("https://raw.githubusercontent.com/acme/bucket.json"),
        ("https://raw.githubusercontent.com/acme/bucket.yaml"),
        ("https://raw.githubusercontent.com/acme/bucket.template")
    ])
    @patch('sceptre.template_handlers.http.Http._get_template')
    def test_handler_raw_template(self, mock_get_template, url):
        mock_get_template.return_value = {}
        handler = Http("http_handler", {'url': url})
        handler.handle()
        assert mock_get_template.call_count == 1

    @patch('sceptre.template_handlers.helper.render_jinja_template')
    @patch('sceptre.template_handlers.http.Http._get_template')
    def test_handler_jinja_template(self, mock_get_template, mock_render_jinja_template):
        mock_get_template_response = {
            "Description": "test template",
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {
                "touchNothing": {
                    "Type": "AWS::CloudFormation::WaitConditionHandle"
                }
            }
        }
        mock_get_template.return_value = json.dumps(mock_get_template_response).encode('utf-8')
        handler = Http("http_handler", {'url': 'https://raw.githubusercontent.com/acme/bucket.j2'})
        handler.handle()
        assert mock_render_jinja_template.call_count == 1

    @patch('sceptre.template_handlers.helper.call_sceptre_handler')
    @patch('sceptre.template_handlers.http.Http._get_template')
    def test_handler_python_template(self, mock_get_template, mock_call_sceptre_handler):
        mock_get_template_response = {
            "Description": "test template",
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {
                "touchNothing": {
                    "Type": "AWS::CloudFormation::WaitConditionHandle"
                }
            }
        }
        mock_get_template.return_value = json.dumps(mock_get_template_response).encode('utf-8')
        handler = Http("http_handler", {'url': 'https://raw.githubusercontent.com/acme/bucket.py'})
        handler.handle()
        assert mock_call_sceptre_handler.call_count == 1

    @patch('sceptre.template_handlers.helper.call_sceptre_handler')
    @patch('sceptre.template_handlers.http.Http._get_template')
    def test_handler_override_handler_options(self, mock_get_template, mock_call_sceptre_handler):
        mock_get_template_response = {
            "Description": "test template",
            "AWSTemplateFormatVersion": "2010-09-09",
            "Resources": {
                "touchNothing": {
                    "Type": "AWS::CloudFormation::WaitConditionHandle"
                }
            }
        }
        mock_get_template.return_value = json.dumps(mock_get_template_response).encode('utf-8')
        custom_handler_options = {"timeout": 10, "retries": 20}
        handler = Http("http_handler",
                       {'url': 'https://raw.githubusercontent.com/acme/bucket.py'},
                       stack_group_config={"http_template_handler": custom_handler_options}
                       )
        handler.handle()
        assert mock_get_template.call_count == 1
        args, options = mock_get_template.call_args
        assert options == {"timeout": 10, "retries": 20}
