import os
import pytest
import yaml

import sceptre.template_handlers.helper as helper
from sceptre.exceptions import TemplateNotFoundError
from unittest.mock import patch


@pytest.mark.parametrize(
    "filename,sceptre_user_data,expected",
    [
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
      Ref: VPC""",
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
      Ref: VPC""",
        ),
        (
            "sg.j2",
            [
                {"name": "sg_a", "inbound_ip": "10.0.0.0"},
                {"name": "sg_b", "inbound_ip": "10.0.0.1"},
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
""",
        ),
    ],
)
@patch("pathlib.Path.exists")
def test_render_jinja_template(mock_pathlib, filename, sceptre_user_data, expected):
    mock_pathlib.return_value = True
    jinja_template_path = os.path.join(
        os.getcwd(), "tests/fixtures/templates", filename
    )
    result = helper.render_jinja_template(
        path=jinja_template_path,
        jinja_vars={"sceptre_user_data": sceptre_user_data},
        j2_environment={},
    )
    expected_yaml = yaml.safe_load(expected)
    result_yaml = yaml.safe_load(result)
    assert expected_yaml == result_yaml


@pytest.mark.parametrize(
    "j2_environment,expected_keys",
    [
        ({}, ["autoescape", "loader", "undefined"]),
        (
            {"lstrip_blocks": True},
            ["autoescape", "loader", "undefined", "lstrip_blocks"],
        ),
        (
            {"lstrip_blocks": True, "extensions": ["test-ext"]},
            ["autoescape", "loader", "undefined", "lstrip_blocks", "extensions"],
        ),
    ],
)
@patch("sceptre.template_handlers.helper.Environment")
@patch("pathlib.Path.exists")
def test_render_jinja_template_j2_environment_config(
    mock_pathlib, mock_environment, j2_environment, expected_keys
):
    mock_pathlib.return_value = True
    filename = "vpc.j2"
    sceptre_user_data = {"vpc_id": "10.0.0.0/16"}
    jinja_template_path = os.path.join(
        os.getcwd(), "tests/fixtures/templates", filename
    )
    _ = helper.render_jinja_template(
        path=jinja_template_path,
        jinja_vars={"sceptre_user_data": sceptre_user_data},
        j2_environment=j2_environment,
    )
    assert list(mock_environment.call_args.kwargs) == expected_keys


def test_render_jinja_template_non_existing_file():
    jinja_template_path = os.path.join("/ref/to/nowhere/boom.j2")
    with pytest.raises(TemplateNotFoundError):
        helper.render_jinja_template(
            path=jinja_template_path,
            jinja_vars={"sceptre_user_data": {}},
            j2_environment={},
        )


@patch("pathlib.Path.exists")
def test_render_jinja_template_with_stack_group_config_and_j2_environment(mock_pathlib):
    """Test that stack_group_config and j2_environment work together in Jinja2 templates."""
    mock_pathlib.return_value = True
    jinja_template_path = os.path.join(
        os.getcwd(), "tests/fixtures/templates", "vpc_with_config.j2"
    )
    jinja_vars = {
        "sceptre_user_data": {"vpc_cidr": "10.0.0.0/16"},
        "stack_group_config": {
            "project_code": "my_project",
            "region": "us-east-1",
        },
    }
    j2_environment = {
        "lstrip_blocks": True,
        "trim_blocks": True,
    }
    result = helper.render_jinja_template(
        path=jinja_template_path,
        jinja_vars=jinja_vars,
        j2_environment=j2_environment,
    )
    result_yaml = yaml.safe_load(result)
    assert result_yaml["Description"] == "VPC for my_project in us-east-1"
    assert result_yaml["Resources"]["VPC"]["Properties"]["CidrBlock"] == "10.0.0.0/16"
    assert (
        result_yaml["Resources"]["VPC"]["Properties"]["Tags"][0]["Value"]
        == "my_project"
    )
