# -*- coding: utf-8 -*-

import json
import yaml
import os
import threading

import pytest
from mock import patch, sentinel, Mock

from freezegun import freeze_time
from botocore.exceptions import ClientError

import sceptre.template
from sceptre.template import Template
from sceptre.connection_manager import ConnectionManager
from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.exceptions import TemplateSceptreHandlerError


class TestTemplate(object):

    def setup_method(self, test_method):
        self.region = "region"
        self.bucket_name = "bucket_name"
        self.environment_path = "environment_path"
        self.stack_name = "stack_name"

        self.connection_manager = Mock(spec=ConnectionManager)
        self.connection_manager.create_bucket_lock = threading.Lock()

        self.template = Template(
            path="/folder/template.py",
            sceptre_user_data={}
        )

    def test_initialise_template(self):
        assert self.template.path == "/folder/template.py"
        assert self.template.name == "template"
        assert self.template.sceptre_user_data == {}
        assert self.template._body is None

    def test_repr(self):
        representation = self.template.__repr__()
        assert representation == "sceptre.template.Template(" \
            "name='template', path='/folder/template.py'"\
            ", sceptre_user_data={})"

    def test_body_with_cache(self):
        self.template._body = sentinel.body
        body = self.template.body
        assert body == sentinel.body

    @freeze_time("2012-01-01")
    @patch("sceptre.template.Template._bucket_exists")
    def test_upload_to_s3_with_valid_arguments(self, mock_bucket_exists):
        self.template._body = '{"template": "mock"}'
        mock_bucket_exists.return_value = True

        url = self.template.upload_to_s3(
            region="eu-west-1",
            bucket_name="bucket-name",
            key_prefix="/prefix/",
            environment_path="environment/path",
            stack_name="stack-name",
            connection_manager=self.connection_manager
        )

        expected_template_key = (
            "prefix/eu-west-1/environment/path/"
            "stack-name-2012-01-01-00-00-00-000000Z.json"
        )

        self.connection_manager.call.assert_called_once_with(
            service="s3",
            command="put_object",
            kwargs={
                "Bucket": "bucket-name",
                "Key": expected_template_key,
                "Body": '{"template": "mock"}',
                "ServerSideEncryption": "AES256"
            }
        )

        assert url == "https://bucket-name.s3.amazonaws.com/{0}".format(
            expected_template_key
        )

    def test_bucket_exists_with_bucket_that_exists(self):
        # connection_manager.call doesn't raise an exception, mimicing the
        # behaviour when head_bucket successfully executes.
        self.template._bucket_exists("bucket_name", self.connection_manager)

    def test_create_bucket_with_unreadable_bucket(self):
        self.connection_manager.call.side_effect = ClientError(
                {
                    "Error": {
                        "Code": 500,
                        "Message": "Bucket Unreadable"
                    }
                },
                sentinel.operation
            )
        with pytest.raises(ClientError) as e:
            self.template._create_bucket(
                "region", "bucket_name", self.connection_manager
            )
            assert e.value.response["Error"]["Code"] == 500
            assert e.value.response["Error"]["Message"] == "Bucket Unreadable"

    def test_bucket_exists_with_non_existent_bucket(self):
        # connection_manager.call is called twice, and should throw the
        # Not Found ClientError only for the first call.
        self.connection_manager.call.side_effect = [
            ClientError(
                {
                    "Error": {
                        "Code": 404,
                        "Message": "Not Found"
                    }
                },
                sentinel.operation
            ),
            None
        ]

        existance = self.template._bucket_exists(
            self.bucket_name,
            self.connection_manager
        )

        assert existance is False

    def test_create_bucket_in_us_east_1(self):
        # connection_manager.call is called twice, and should throw the
        # Not Found ClientError only for the first call.

        self.template._create_bucket(
            "us-east-1",
            self.bucket_name,
            self.connection_manager
        )

        self.connection_manager.call.assert_any_call(
            service="s3",
            command="create_bucket",
            kwargs={"Bucket": self.bucket_name}
        )

    def test_body_with_json_template(self):
        self.template.name = "vpc"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc.json"
        )
        output = self.template.body
        output_dict = json.loads(output)
        with open("tests/fixtures/templates/compiled_vpc.json", "r") as f:
            expected_output_dict = json.loads(f.read())
        assert output_dict == expected_output_dict

    def test_body_with_yaml_template(self):
        self.template.name = "vpc"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc.yaml"
        )
        output = self.template.body
        output_dict = yaml.load(output)
        with open("tests/fixtures/templates/compiled_vpc.json", "r") as f:
            expected_output_dict = json.loads(f.read())
        assert output_dict == expected_output_dict

    def test_body_with_missing_file(self):
        self.template.path = "incorrect/template/path.py"
        with pytest.raises(IOError):
            self.template.body

    def test_body_with_python_template(self):
        self.template.sceptre_user_data = None
        self.template.name = "vpc"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc.py"
        )
        actual_output = json.loads(self.template.body)
        with open("tests/fixtures/templates/compiled_vpc.json", "r") as f:
            expected_output = json.loads(f.read())
        assert actual_output == expected_output

    def test_body_with_python_template_with_sgt(self):
        self.template.sceptre_user_data = None
        self.template.name = "vpc_sgt"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc_sgt.py"
        )
        actual_output = json.loads(self.template.body)
        with open("tests/fixtures/templates/compiled_vpc.json", "r") as f:
            expected_output = json.loads(f.read())
        assert actual_output == expected_output

    def test_body_injects_sceptre_user_data(self):
        self.template.sceptre_user_data = {
            "cidr_block": "10.0.0.0/16"
        }
        self.template.name = "vpc_sud"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc_sud.py"
        )

        actual_output = json.loads(self.template.body)
        with open("tests/fixtures/templates/compiled_vpc_sud.json", "r") as f:
            expected_output = json.loads(f.read())
        assert actual_output == expected_output

    def test_body_injects_sceptre_user_data_incorrect_function(self):
        self.template.sceptre_user_data = {
            "cidr_block": "10.0.0.0/16"
        }
        self.template.name = "vpc_sud_incorrect_function"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc_sud_incorrect_function.py"
        )
        with pytest.raises(TemplateSceptreHandlerError):
            self.template.body

    def test_body_injects_sceptre_user_data_incorrect_handler(self):
        self.template.sceptre_user_data = {
            "cidr_block": "10.0.0.0/16"
        }
        self.template.name = "vpc_sud_incorrect_handler"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc_sud_incorrect_handler.py"
        )
        with pytest.raises(TypeError):
            self.template.body

    def test_body_with_incorrect_filetype(self):
        self.template.path = (
            "path/to/something.ext"
        )
        with pytest.raises(UnsupportedTemplateFileTypeError):
            self.template.body


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
    result = sceptre.template.Template._render_jinja_template(
        template_dir=jinja_template_dir,
        filename=filename,
        jinja_vars={"sceptre_user_data": sceptre_user_data}
    )
    expected_yaml = yaml.safe_load(expected)
    result_yaml = yaml.safe_load(result)
    assert expected_yaml == result_yaml
