# -*- coding: utf-8 -*-

from behave import *
import subprocess
import json


@given("the generate-parameter-file command is run")
def step_impl(context):
    context.param_json = subprocess.check_output([
        "sceptre", "--dir", context.sceptre_dir, "generate-parameters-file",
        "test-env/a", "vpc"
    ])


@then("the parameters file json syntax is correct")
def step_impl(context):
    context.param_json = \
        json.loads(context.template_json_str.decode("utf8"))


@then("the parameters file contains a valid cidr range")
def step_impl(context):
    assert(context.param_json \
        ["Resources"]["VirtualPrivateCloud"]["Type"] == \
        "AWS::EC2::VPC"
    )
