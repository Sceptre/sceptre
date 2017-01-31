from behave import *
import subprocess
import boto3


@when("we run delete stack")
def step_impl(context):
    subprocess.call(
        ["sceptre", "delete-stack", "test-env/a", "wait-condition-handle"]
    )


@then("the stack is deleted")
def step_impl(context):
    client = boto3.client("cloudformation")
    response = client.describe_stacks()
    stack_names = [stack["StackName"] for stack in response["Stacks"]]
    assert "{0}-{1}-wait-condition-handle".format(
        context.project_code, context.environment_path_a
    ) not in stack_names
