import os

import pytest
import yaml

from sceptre.template_handlers.file import File


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
    result = File._render_jinja_template(
        template_dir=jinja_template_dir,
        filename=filename,
        jinja_vars={"sceptre_user_data": sceptre_user_data}
    )
    expected_yaml = yaml.safe_load(expected)
    result_yaml = yaml.safe_load(result)
    assert expected_yaml == result_yaml
