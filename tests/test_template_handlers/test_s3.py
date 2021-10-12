# -*- coding: utf-8 -*-
import json
import io
import pytest

from mock import MagicMock
from sceptre.connection_manager import ConnectionManager
from sceptre.exceptions import SceptreException, UnsupportedTemplateFileTypeError
from sceptre.template_handlers.s3 import S3
from unittest.mock import patch


class TestS3(object):

    def test_get_template(self):
        connection_manager = MagicMock(spec=ConnectionManager)
        connection_manager.call.return_value = {
            "Body": io.BytesIO(b"Stuff is working")
        }
        template_handler = S3(
            name="s3_handler",
            arguments={"path": "bucket/folder/file.yaml"},
            connection_manager=connection_manager
        )
        result = template_handler.handle()

        connection_manager.call.assert_called_once_with(
            service="s3",
            command="get_object",
            kwargs={
                "Bucket": "bucket",
                "Key": "folder/file.yaml"
            }
        )
        assert result == b"Stuff is working"

    def test_template_handler(self):
        connection_manager = MagicMock(spec=ConnectionManager)
        connection_manager.call.return_value = {
            "Body": io.BytesIO(b"Stuff is working")
        }
        template_handler = S3(
            name="vpc",
            arguments={"path": "my-fancy-bucket/account/vpc.yaml"},
            connection_manager=connection_manager
        )
        result = template_handler.handle()

        connection_manager.call.assert_called_once_with(
            service="s3",
            command="get_object",
            kwargs={
                "Bucket": "my-fancy-bucket",
                "Key": "account/vpc.yaml"
            }
        )
        assert result == b"Stuff is working"

    def test_invalid_response_reraises_exception(self):
        connection_manager = MagicMock(spec=ConnectionManager)
        connection_manager.call.side_effect = SceptreException("BOOM!")

        template_handler = S3(
            name="vpc",
            arguments={"path": "my-fancy-bucket/account/vpc.yaml"},
            connection_manager=connection_manager
        )

        with pytest.raises(SceptreException) as e:
            template_handler.handle()

        assert str(e.value) == "BOOM!"

    def test_handler_unsupported_type(self):
        s3_handler = S3("s3_handler", {'path': 'bucket/folder/file.unsupported'})
        with pytest.raises(UnsupportedTemplateFileTypeError):
            s3_handler.handle()

    @pytest.mark.parametrize("path", [
        ("bucket/folder/file.json"),
        ("bucket/folder/file.yaml"),
        ("bucket/folder/file.template")
    ])
    @patch('sceptre.template_handlers.s3.S3._get_template')
    def test_handler_raw_template(self, mock_get_template, path):
        mock_get_template.return_value = {}
        s3_handler = S3("s3_handler", {'path': path})
        s3_handler.handle()
        assert mock_get_template.call_count == 1

    @patch('sceptre.template_handlers.helper.render_jinja_template')
    @patch('sceptre.template_handlers.s3.S3._get_template')
    def test_handler_jinja_template(slef, mock_get_template, mock_render_jinja_template):
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
        s3_handler = S3("s3_handler", {'path': 'bucket/folder/file.py'})
        s3_handler.handle()
        assert mock_call_sceptre_handler.call_count == 1
