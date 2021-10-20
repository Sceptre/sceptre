import os
import pytest
import yaml

import sceptre.template_handlers.helper as helper
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
    result = helper.render_jinja_template(
        template_dir=jinja_template_dir,
        filename=filename,
        jinja_vars={"sceptre_user_data": sceptre_user_data},
        stack_group_config={}
    )
    expected_yaml = yaml.safe_load(expected)
    result_yaml = yaml.safe_load(result)
    assert expected_yaml == result_yaml


@pytest.mark.parametrize("stack_group_config,expected_keys", [
    ({}, ["autoescape", "loader", "undefined"]),
    ({"j2_environment": {"lstrip_blocks": True}},
     ["autoescape", "loader", "undefined", "lstrip_blocks"]),
    ({"j2_environment": {"lstrip_blocks": True, "extensions": ["test-ext"]}},
     ["autoescape", "loader", "undefined", "lstrip_blocks", "extensions"])
])
@patch("sceptre.template_handlers.helper.Environment")
def test_render_jinja_template_j2_environment_config(mock_environment, stack_group_config, expected_keys):
    filename = "vpc.j2"
    sceptre_user_data = {"vpc_id": "10.0.0.0/16"}
    jinja_template_dir = os.path.join(
        os.getcwd(),
        "tests/fixtures/templates"
    )
    _ = helper.render_jinja_template(
        template_dir=jinja_template_dir,
        filename=filename,
        jinja_vars={"sceptre_user_data": sceptre_user_data},
        stack_group_config=stack_group_config
    )
    assert list(mock_environment.call_args.kwargs) == expected_keys
