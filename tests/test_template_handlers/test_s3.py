import json
import pytest
import os
import yaml

from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers.s3 import S3
from unittest.mock import patch


@pytest.mark.parametrize("filename,sceptre_user_data,expected", [
    (
        "vpc.j2",
        {"vpc_id": "10.0.0.0/16"},
        """Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
Outputs:
  VpcId:
    Value:
      Ref: VPC"""
    ),
    (
        "vpc.yaml.j2",
        {"vpc_id": "10.0.0.0/16"},
        """Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
Outputs:
  VpcId:
    Value:
      Ref: VPC"""
    ),
    (
        "sg.j2",
        [
            {"name": "sg_a", "inbound_ip": "10.0.0.0"},
            {"name": "sg_b", "inbound_ip": "10.0.0.1"}
        ],
        """Resources:
    sg_a:
        Type: "AWS::EC2::SecurityGroup"
        Properties:
            InboundIp: 10.0.0.0
    sg_b:
        Type: "AWS::EC2::SecurityGroup"
        Properties:
            InboundIp: 10.0.0.1
"""
    )
])
def test_render_jinja_template(filename, sceptre_user_data, expected):
    jinja_template_dir = os.path.join(
        os.getcwd(),
        "tests/fixtures/templates"
    )
    result = S3._render_jinja_template(
        template_dir=jinja_template_dir,
        filename=filename,
        jinja_vars={"sceptre_user_data": sceptre_user_data}
    )
    expected_yaml = yaml.safe_load(expected)
    result_yaml = yaml.safe_load(result)
    assert expected_yaml == result_yaml


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


@patch('sceptre.template_handlers.s3.S3._render_jinja_template')
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


@patch('sceptre.template_handlers.s3.S3._call_sceptre_handler')
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
