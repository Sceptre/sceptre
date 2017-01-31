from behave import *
import subprocess
import boto3


@when("we run launch env")
def step_impl(context):
    subprocess.call(["sceptre", "launch-env", "test-env"])


@then("an env is created")
def step_impl(context):
    client = boto3.client("cloudformation")

    response = client.describe_stacks()
    integraion_test_stacks = [
        stack["StackName"] for stack in response["Stacks"]
        if context.project_code in stack["StackName"]
    ]

    expected_stacks = [
        "{0}-{1}-security-group".format(
            context.project_code, context.environment_path_a
        ),
        "{0}-{1}-vpc".format(context.project_code, context.environment_path_a),
        "{0}-{1}-wait-condition-handle".format(
            context.project_code, context.environment_path_a
        ),
        "{0}-{1}-security-group".format(
            context.project_code, context.environment_path_b
        ),
        "{0}-{1}-wait-condition-handle".format(
            context.project_code, context.environment_path_b
        )
    ]

    assert sorted(expected_stacks) == sorted(integraion_test_stacks)

    integration_test_statuses = [
        stack["StackStatus"] for stack in response["Stacks"]
        if stack["StackName"] in integraion_test_stacks
    ]

    for status in integration_test_statuses:
        assert status == "CREATE_COMPLETE"
