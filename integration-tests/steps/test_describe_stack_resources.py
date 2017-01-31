# -*- coding: utf-8 -*-

from behave import *
import subprocess
import yaml


@then("the stack resources are listed")
def step_impl(context):
    raw_response = subprocess.check_output([
        "sceptre", "describe-stack-resources",
        "test-env/a", "wait-condition-handle"
    ])
    response = yaml.safe_load(raw_response)
    assert response[0]["LogicalResourceId"] == \
        "WaitConditionHandle"
