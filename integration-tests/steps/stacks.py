from behave import *
import json
import time
import os
import boto3
from botocore.exceptions import ClientError, WaiterError
from sceptre.environment import Environment


def wait_for_final_state(context, stack_name):
    stack = context.cloudformation.Stack(stack_name)
    delay = 2
    max_retries = 10
    attempts = 0
    while attempts < max_retries:
        stack.load()
        if not stack.stack_status.endswith("IN_PROGRESS"):
            return
        time.sleep(delay)
    raise Exception("Timeout waiting for stack to reach final state.")


def before_all(context):
    context.cloudformation = boto3.resource('cloudformation')
    context.client = boto3.client("cloudformation")
    context.sceptre_dir = os.path.join(
        os.getcwd(), "integration-tests", "sceptre-project"
    )
    context.default_environment = "default"
    context.error = None


def before_step(context, step):
    context.error = None


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
            body = generate_template(path, "valid")
            create_stack(context, full_name, body)
        elif desired_status == "CREATE_FAILED":
            body = generate_template(path, "invalid")
            kwargs = {"OnFailure": "DO_NOTHING"}
            create_stack(context, full_name, body, **kwargs)
        elif desired_status == "UPDATE_COMPLETE":
            body = generate_template(path, "valid")
            create_stack(context, full_name, body)
            body = generate_template(path, "updated")
            update_stack(context, full_name, body)
        elif desired_status == "ROLLBACK_COMPLETE":
            body = generate_template(path, "invalid")
            kwargs = {"OnFailure": "ROLLBACK"}
            create_stack(context, full_name, body, **kwargs)

    status = get_stack_status(context, full_name)
    assert (status == desired_status)


@given('the template for stack "{stack_name}" is {modification}')
def step_impl(context, stack_name, modification):
    path = os.path.join(
        context.sceptre_dir, "templates", "wait_condition_handle.json"
    )

    body = generate_template(path, modification)

    with open(path, 'w') as template:
        template.write(body)


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


@when('the user updates stack "{stack_name}"')
def step_impl(context, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)

    try:
        env.stacks[stack_name].update()
    except ClientError as e:
        message = e.response['Error']['Message']
        if e.response['Error']['Code'] == 'ValidationError' \
            and (message.endswith("does not exist")
                 or message.endswith("No updates are to be performed.")):
            return
        else:
            raise e


@when('the user deletes stack "{stack_name}"')
def step_impl(context, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)
    try:
        env.stacks[stack_name].delete()
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError' \
          and e.response['Error']['Message'].endswith("does not exist"):
            return
        else:
            raise e


@when('the user launches stack "{stack_name}"')
def step_impl(context, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)

    env.stacks[stack_name].launch()


@then('stack "{stack_name}" exists in "{desired_status}" state')
def step_impl(context, stack_name, desired_status):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    status = get_stack_status(context, full_name)
    assert (status == desired_status)


@then('stack "{stack_name}" does not exist')
def step_impl(context, stack_name):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    status = get_stack_status(context, full_name)
    assert (status is None)


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


def generate_template(path, modification):
    if modification == "valid":
        data = {
            "Resources": {
                "WaitConditionHandle": {
                    "Type": "AWS::CloudFormation::WaitConditionHandle",
                    "Properties": {}
                }
            }
        }
    elif modification == "invalid":
        data = {
            "Resources": {
                "WaitConditionHandle": {
                    "Type": "AWS::CloudFormation::WaitConditionHandle",
                    "Properties": {}
                },
                "InvalidWaitConditionHandle": {
                    "Type": "AWS::CloudFormation::WaitConditionHandle",
                    "Properties": {
                        "Invalid": "Invalid"
                    }
                }
            }
        }
    elif modification == "updated":
        data = {
            "Resources": {
                "WaitConditionHandle": {
                    "Type": "AWS::CloudFormation::WaitConditionHandle",
                    "Properties": {}
                },
                "AnotherWaitConditionHandle": {
                    "Type": "AWS::CloudFormation::WaitConditionHandle",
                    "Properties": {}
                }
            }
        }

    return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))


def create_stack(context, stack_name, body, **kwargs):
    context.client.create_stack(
        StackName=stack_name, TemplateBody=body, **kwargs
    )

    wait_for_final_state(context, stack_name)


def update_stack(context, stack_name, body, **kwargs):
    stack = context.cloudformation.Stack(stack_name)
    stack.update(TemplateBody=body, **kwargs)

    wait_for_final_state(context, stack_name)


def delete_stack(context, stack_name):
    stack = context.cloudformation.Stack(stack_name)
    stack.delete()

    waiter = context.client.get_waiter('stack_delete_complete')
    waiter.config.delay = 2
    waiter.wait(StackName=stack_name)
