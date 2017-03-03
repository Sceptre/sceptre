# -*- coding: utf-8 -*-

import json
import yaml
import os
import threading

import pytest
from mock import patch, sentinel, Mock

from freezegun import freeze_time
from botocore.exceptions import ClientError

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

    @patch("sceptre.template.Template._get_body")
    def test_body_without_cache(self, mock_get_body):
        self.template._body = None
        mock_get_body.return_value = sentinel.body
        body = self.template.body
        assert body == sentinel.body

    @freeze_time("2012-01-01")
    @patch("sceptre.template.Template._create_bucket")
    def test_upload_to_s3_with_valid_arguments(self, mock_create_bucket):
        self.template._body = '{"template": "mock"}'

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

        mock_create_bucket.assert_called_once_with(
            "eu-west-1", "bucket-name", self.connection_manager
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

    def test_create_bucket_with_bucket_that_exists(self):
        # connection_manager.call doesn't raise an exception, mimicing the
        # behaviour when head_bucket successfully executes.
        self.template._create_bucket(
            "region", "bucket_name", self.connection_manager
        )

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

    def test_create_bucket_with_non_existent_bucket(self):
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

        self.template._create_bucket(
            self.region,
            self.bucket_name,
            self.connection_manager
        )

        self.connection_manager.call.assert_any_call(
            service="s3",
            command="create_bucket",
            kwargs={
                "Bucket": self.bucket_name,
                "CreateBucketConfiguration": {
                    "LocationConstraint": self.region
                },
            }
        )

    def test_create_bucket_with_non_existent_us_east_1_bucket(self):
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

    def test_get_body_with_json_template(self):
        self.template.name = "vpc"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc.json"
        )
        output = self.template._get_body()
        output_dict = json.loads(output)
        with open("tests/fixtures/templates/compiled_vpc.json", "r") as f:
            expected_output_dict = json.loads(f.read())
        assert output_dict == expected_output_dict

    def test_get_body_with_yaml_template(self):
        self.template.name = "vpc"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc.yaml"
        )
        output = self.template._get_body()
        output_dict = yaml.load(output)
        with open("tests/fixtures/templates/compiled_vpc.json", "r") as f:
            expected_output_dict = json.loads(f.read())
        assert output_dict == expected_output_dict

    def test_get_body_with_missing_file(self):
        self.template.path = "incorrect/template/path.py"
        with pytest.raises(IOError):
            self.template._get_body()

    def test_get_body_compiles_troposphere(self):
        self.template.sceptre_user_data = None
        self.template.name = "vpc"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc.py"
        )
        output = self.template._get_body()
        try:
            json.loads(output)
        except:
            assert False

    def test_get_body_with_troposphere(self):
        self.template.sceptre_user_data = None
        self.template.name = "vpc"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc.py"
        )
        actual_output = json.loads(self.template._get_body())
        with open("tests/fixtures/templates/compiled_vpc.json", "r") as f:
            expected_output = json.loads(f.read())
        assert actual_output == expected_output

    def test_get_body_with_troposphere_with_sgt(self):
        self.template.sceptre_user_data = None
        self.template.name = "vpc_sgt"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc_sgt.py"
        )
        actual_output = json.loads(self.template._get_body())
        with open("tests/fixtures/templates/compiled_vpc.json", "r") as f:
            expected_output = json.loads(f.read())
        assert actual_output == expected_output

    def test_get_body_injects_sceptre_user_data(self):
        self.template.sceptre_user_data = {
            "cidr_block": "10.0.0.0/16"
        }
        self.template.name = "vpc_sud"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc_sud.py"
        )

        actual_output = json.loads(self.template._get_body())
        with open("tests/fixtures/templates/compiled_vpc_sud.json", "r") as f:
            expected_output = json.loads(f.read())
        assert actual_output == expected_output

    def test_get_body_injects_sceptre_user_data_incorrect_function(self):
        self.template.sceptre_user_data = {
            "cidr_block": "10.0.0.0/16"
        }
        self.template.name = "vpc_sud_incorrect_function"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc_sud_incorrect_function.py"
        )
        with pytest.raises(TemplateSceptreHandlerError):
            self.template._get_body()

    def test_get_body_injects_sceptre_user_data_incorrect_handler(self):
        self.template.sceptre_user_data = {
            "cidr_block": "10.0.0.0/16"
        }
        self.template.name = "vpc_sud_incorrect_handler"
        self.template.path = os.path.join(
            os.getcwd(),
            "tests/fixtures/templates/vpc_sud_incorrect_handler.py"
        )
        with pytest.raises(TypeError):
            self.template._get_body()

    def test_get_body_with_incorrect_filetype(self):
        self.template.path = (
            "path/to/something.ext"
        )
        with pytest.raises(UnsupportedTemplateFileTypeError):
            self.template._get_body()
