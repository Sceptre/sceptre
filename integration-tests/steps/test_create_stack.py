from behave import *
import subprocess
import boto3


@when("we run create stack")
def step_impl(context):
    subprocess.call(
        ["sceptre", "create-stack", "test-env/a", "wait-condition-handle"]
    )


@then("a stack is created")
def step_impl(context):
    client = boto3.client("cloudformation")
    response = client.describe_stacks(
        StackName="{0}-{1}-wait-condition-handle".format(
            context.project_code, context.environment_path_a
        )
    )
    assert response["Stacks"][0]["StackStatus"] == "CREATE_COMPLETE"


@then("all its resources are created")
def step_impl(context):
    client = boto3.client("cloudformation")
    response = client.describe_stack_resources(
        StackName="{0}-{1}-wait-condition-handle".format(
            context.project_code, context.environment_path_a
        )
    )

    resource_statuses = [
        resource["ResourceStatus"] for resource in response["StackResources"]
    ]

    for status in resource_statuses:
        assert status == "CREATE_COMPLETE"
