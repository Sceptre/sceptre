import json
import pytest

from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers.s3 import S3
from unittest.mock import patch


def test_handler_unsupported_type():
    s3_handler = S3("s3_handler", {'path': 'bucket/folder/file.unsupported'})
    with pytest.raises(UnsupportedTemplateFileTypeError):
        s3_handler.handle()


@pytest.mark.parametrize("path", [
    ("bucket/folder/file.json"),
    ("bucket/folder/file.yaml"),
    ("bucket/folder/file.template")
])
@patch('sceptre.template_handlers.s3.S3._get_template')
def test_handler_raw_template(mock_get_template, path):
    mock_get_template.return_value = {}
    s3_handler = S3("s3_handler", {'path': path})
    s3_handler.handle()
    assert mock_get_template.call_count == 1


@patch('sceptre.template_handlers.helper.render_jinja_template')
@patch('sceptre.template_handlers.s3.S3._get_template')
def test_handler_jinja_template(mock_get_template, mock_render_jinja_template):
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
    s3_handler = S3("s3_handler", {'path': 'bucket/folder/file.j2'})
    s3_handler.handle()
    assert mock_render_jinja_template.call_count == 1


@patch('sceptre.template_handlers.helper.call_sceptre_handler')
@patch('sceptre.template_handlers.s3.S3._get_template')
def test_handler_python_template(mock_get_template, mock_call_sceptre_handler):
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
    s3_handler = S3("s3_handler", {'path': 'bucket/folder/file.py'})
    s3_handler.handle()
    assert mock_call_sceptre_handler.call_count == 1
