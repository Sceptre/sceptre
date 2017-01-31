# -*- coding: utf-8 -*-

from behave import *
import subprocess
import yaml


@then("the env is described")
def step_impl(context):
    raw_response = subprocess.check_output([
        "sceptre", "describe-env", "test-env"
    ])
    response = yaml.safe_load(raw_response)

    # Note wait-condition-handle isn't created by the step given some stacks
    # exist
    expected_response = {
        "test-env/a/security-group": "CREATE_COMPLETE",
        "test-env/a/vpc": "CREATE_COMPLETE",
        "test-env/a/wait-condition-handle": "PENDING",
        "test-env/b/security-group": "CREATE_COMPLETE",
        "test-env/b/wait-condition-handle": "PENDING"
    }

    assert response == expected_response


@then("the env resources are described")
def step_impl(context):
    raw_response = subprocess.check_output([
        "sceptre", "describe-env-resources", "test-env"
    ])
    response = yaml.safe_load(raw_response)

    # Remove the PhysicalResourceId attrubite from the response, as it's
    # dynamically allocated by AWS and cannot be predicted.
    for resources in response.values():
        for resource in resources:
            del(resource["PhysicalResourceId"])

    expected_response = {
        "test-env/a/security-group": [{"LogicalResourceId": "SecurityGroup"}],
        "test-env/a/vpc": [{"LogicalResourceId": "VirtualPrivateCloud"}],
        "test-env/b/security-group": [{"LogicalResourceId": "SecurityGroup"}]
    }

    assert sorted(response) == sorted(expected_response)
