from behave import *
import json
import os
import boto3
from botocore.exceptions import ClientError, WaiterError
from sceptre.environment import Environment


def before_all(context):
    context.cloudformation = boto3.resource('cloudformation')
    context.client = boto3.client("cloudformation")
    context.sceptre_dir = os.path.join(
        os.getcwd(), "integration-tests", "sceptre-project"
    )
    context.default_environment = "default"


@given('stack "{stack_name}" does not exist')
def step_impl(context, stack_name):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    status = get_stack_status(context, full_name)
    if status is not None:
        delete_stack(context, full_name)
    status = get_stack_status(context, full_name)
    assert (status is None)


@given('stack "{stack_name}" exists in "{desired_status}" state')
def step_impl(context, stack_name, desired_status):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    path = os.path.join(
        context.sceptre_dir, "templates", "wait_condition_handle.json"
    )

    status = get_stack_status(context, full_name)
    if status != desired_status:
        delete_stack(context, full_name)
        if desired_status == "CREATE_COMPLETE":
            body = generate_template(path)
            create_stack(context.client, full_name, body)
        elif desired_status == "CREATE_FAILED":
            body = generate_template(path, invaild_resource=True)
            kwargs = {"OnFailure": "DO_NOTHING"}
            create_stack(context.client, full_name, body, **kwargs)
        elif desired_status == "ROLLBACK_COMPLETE":
            body = generate_template(path, invaild_resource=True)
            kwargs = {"OnFailure": "ROLLBACK"}
            create_stack(context.client, full_name, body, **kwargs)

    status = get_stack_status(context, full_name)
    print("Comparision " + status + " " + desired_status)
    assert (status == desired_status)


@when('the user creates stack "{stack_name}"')
def step_impl(context, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)
    try:
        env.stacks[stack_name].create()
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException' \
        and e.response['Error']['Message'].endswith("already exists"):
            return
        else:
            raise e

@then('stack "{stack_name}" exists in "{desired_status}" state')
def step_impl(context, stack_name, desired_status):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    status = get_stack_status(context, full_name)
    print("Comparision " + status + " " + desired_status)
    print(status == desired_status)
    assert (status == desired_status)


def get_stack_status(context, stack_name):
    try:
        stack = context.cloudformation.Stack(stack_name)
        stack.load()
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError' \
        and e.response['Error']['Message'].endswith("does not exist"):
            return None
        else:
            raise e
    return stack.stack_status


def generate_template(path, invaild_resource=False):
    with open(path) as template:
        data = json.load(template)

    if invaild_resource:
        invaild_resource = {
            "InvalidWaitConditionHandle": {
                "Type": "AWS::CloudFormation::WaitConditionHandle",
                "Properties": {
                  "Invalid": "Invalid"
                }
            }
        }

        data["Resources"].update(invaild_resource)
    return json.dumps(data)


def create_stack(client, stack_name, body, **kwargs):
    response = client.create_stack(
        StackName=stack_name, TemplateBody=body, **kwargs
    )

    waiter = client.get_waiter('stack_create_complete')
    for acceptor in waiter.config.acceptors:
        if acceptor.expected == "CREATE_FAILED":
            print(acceptor.state)
    waiter.config.delay = 2
    waiter.wait(StackName=stack_name)


def delete_stack(context, stack_name):
    stack = context.cloudformation.Stack(stack_name)
    stack.delete()

    waiter = context.client.get_waiter('stack_delete_complete')
    waiter.config.delay = 2
    try:
        waiter.wait(StackName=stack_name)
    except WaiterError as e:
        print(e)
