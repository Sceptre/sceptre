from behave import *
import subprocess
import boto3


@when("we run delete env")
def step_impl(context):
    subprocess.call([
        "sceptre", "--dir", context.sceptre_dir, "delete-env", "test-env"
    ])


@then("the env is deleted")
def step_impl(context):
    client = boto3.client("cloudformation")
    response = client.describe_stacks()

    integraion_test_stacks = [
        stack["StackName"] for stack in response["Stacks"]
        if context.project_code in stack["StackName"]
    ]
    assert integraion_test_stacks == []
