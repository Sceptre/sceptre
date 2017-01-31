# -*- coding: utf-8 -*-

from behave import *
import subprocess
import json


@given("the generate-template command is run")
def step_impl(context):
    context.template_json_str = subprocess.check_output([
        "sceptre", "generate-template", "test-env/a", "vpc"
    ])


@then("the template json syntax is correct")
def step_impl(context):
    context.template_json = \
        json.loads(context.template_json_str.decode("utf8"))


@then("the template contains a vpc")
def step_impl(context):
    assert(context.template_json \
        ["Resources"]["VirtualPrivateCloud"]["Type"] == \
        "AWS::EC2::VPC"
    )
