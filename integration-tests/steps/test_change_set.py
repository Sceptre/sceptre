from behave import *
import subprocess
import boto3
import time
import yaml
import os


@when("we run create change set")
def step_impl(context):
    subprocess.call([
        "sceptre", "create-change-set", "test-env/a", "vpc", "test-change-set"
    ])
    # Wait for change set to be created
    time.sleep(5)


@then("the stack contains a change set")
def step_impl(context):
    client = boto3.client("cloudformation")
    response = client.describe_change_set(
        StackName="{0}-{1}-vpc".format(
            context.project_code, context.environment_path_a
        ),
        ChangeSetName="test-change-set"
    )

    assert response["Status"] == "CREATE_COMPLETE"


@then("the change set should be described")
def step_impl(context):
    raw_response = subprocess.check_output([
        "sceptre", "describe-change-set", "test-env/a",
        "vpc", "test-change-set"
    ])

    response = yaml.safe_load(raw_response)

    # CreationTime cannot be pre-determined.
    assert "CreationTime" in response
    del response["CreationTime"]

    assert response == {
        "ChangeSetName": "test-change-set",
        "Changes": [
            {
                "ResourceChange": {
                    "Action": "Add",
                    "LogicalResourceId": "IGWAttachment",
                    "ResourceType": "AWS::EC2::VPCGatewayAttachment"
                }
            },
            {
                "ResourceChange": {
                    "Action": "Add",
                    "LogicalResourceId": "InternetGateway",
                    "ResourceType": "AWS::EC2::InternetGateway"
                }
            }
        ],
        "ExecutionStatus": "AVAILABLE",
        "StackName": "{0}-{1}-vpc".format(
            context.project_code, context.environment_path_a
        ),
        "Status": "CREATE_COMPLETE"
    }


@then("the change set can be listed")
def step_impl(context):
    raw_response = subprocess.check_output([
        "sceptre", "list-change-sets", "test-env/a", "vpc"
    ])

    response = yaml.safe_load(raw_response)

    assert response["Summaries"][0]["ChangeSetName"] == "test-change-set"


@when("the change set is executed")
def step_impl(context):
    subprocess.call([
        "sceptre", "execute-change-set", "test-env/a", "vpc", "test-change-set"
    ])


@given("a change set exists in the stack")
def step_impl(context):
    client = boto3.client("cloudformation")
    stack_name = "{0}-{1}-vpc".format(
        context.project_code, context.environment_path_a
    )

    vpc_template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "vpc.json"
    )
    with open(vpc_template_path, "r") as f:
        template = f.read()

    client.create_change_set(
        StackName=stack_name,
        TemplateBody=template,
        Parameters=[{
            "ParameterKey": "CidrBlock",
            "ParameterValue": "10.0.0.0/16",
        }],
        ChangeSetName="test-change-set"
    )

    # Wait for change set to be created
    time.sleep(5)


@when("we execute delete change set")
def step_impl(context):
    subprocess.call([
        "sceptre", "delete-change-set", "test-env/a", "vpc", "test-change-set"
    ])
    # Wait for change set to be deleted
    time.sleep(5)


@then("the change set should not be present in the stack")
def step_impl(context):
    client = boto3.client("cloudformation")
    response = client.list_change_sets(
        StackName="{0}-{1}-vpc".format(
            context.project_code, context.environment_path_a
        )
    )
    assert "test-change-set" not in response["Summaries"]
