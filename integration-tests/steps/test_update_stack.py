from behave import *
import subprocess
import os
import boto3


@when("the stack config is changed")
def step_impl(context):
    # Get config file path
    vpc_config_file = os.path.abspath(os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config",
        "test-env",
        "a",
        "vpc.yaml"
    ))
    with open(vpc_config_file, "r+") as f:
        config = f.read()
    config = config.replace("vpc.py", "updated_vpc.py")
    with open(vpc_config_file, "w") as f:
        f.write(config)


@when("we run update stack")
def step_impl(context):
    subprocess.call(["sceptre", "update-stack", "test-env/a", "vpc"])


@then("the stack is updated")
def step_impl(context):
    client = boto3.client("cloudformation")
    response = client.describe_stacks(
        StackName="{0}-{1}-vpc".format(
            context.project_code, context.environment_path_a
        )
    )
    assert response["Stacks"][0]["StackStatus"] == "UPDATE_COMPLETE"
