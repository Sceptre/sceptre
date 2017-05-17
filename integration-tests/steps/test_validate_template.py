# -*- coding: utf-8 -*-

from behave import *
import subprocess
import yaml


@when("validate template is run")
def step_impl(context):
    context.response = subprocess.check_output([
        "sceptre", "--dir", context.sceptre_dir, "validate-template",
        "test-env/a", "wait-condition-handle"
    ])


@then("the template is marked as valid")
def step_impl(context):
    response_dict = yaml.safe_load(context.response)
    assert response_dict["ResponseMetadata"]["HTTPStatusCode"] == 200
