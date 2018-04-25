from behave import *
import time
import os
from botocore.exceptions import ClientError
from sceptre.environment import Environment
from helpers import read_template_file, get_cloudformation_stack_name
from helpers import retry_boto_call


@given('stack "{stack_name}" does not exist')
def step_impl(context, stack_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    status = get_stack_status(context, full_name)
    if status is not None:
        delete_stack(context, full_name)
    status = get_stack_status(context, full_name)
    assert (status is None)


@given('stack "{stack_name}" exists in "{desired_status}" state')
def step_impl(context, stack_name, desired_status):
    full_name = get_cloudformation_stack_name(context, stack_name)

    status = get_stack_status(context, full_name)
    if status != desired_status:
        delete_stack(context, full_name)
        if desired_status == "CREATE_COMPLETE":
            body = read_template_file(context, "valid_template.json")
            create_stack(context, full_name, body)
        elif desired_status == "CREATE_FAILED":
            body = read_template_file(context, "invalid_template.json")
            kwargs = {"OnFailure": "DO_NOTHING"}
            create_stack(context, full_name, body, **kwargs)
        elif desired_status == "UPDATE_COMPLETE":
            body = read_template_file(context, "valid_template.json")
            create_stack(context, full_name, body)
            body = read_template_file(context, "updated_template.json")
            update_stack(context, full_name, body)
        elif desired_status == "ROLLBACK_COMPLETE":
            body = read_template_file(context, "invalid_template.json")
            kwargs = {"OnFailure": "ROLLBACK"}
            create_stack(context, full_name, body, **kwargs)

    status = get_stack_status(context, full_name)
    assert (status == desired_status)


@given('stack "{stack_name}" exists using "{template_name}"')
def step_impl(context, stack_name, template_name):
    full_name = get_cloudformation_stack_name(context, stack_name)

    status = get_stack_status(context, full_name)
    if status != "CREATE_COMPLETE":
        delete_stack(context, full_name)
        body = read_template_file(context, template_name)
        create_stack(context, full_name, body)

    status = get_stack_status(context, full_name)
    assert (status == "CREATE_COMPLETE")


@when('the user creates stack "{stack_name}"')
def step_impl(context, stack_name):
    environment_name, _ = os.path.split(stack_name)
    env = Environment(context.sceptre_dir, environment_name)
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
    environment_name, _ = os.path.split(stack_name)
    env = Environment(context.sceptre_dir, environment_name)
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
    environment_name, _ = os.path.split(stack_name)
    env = Environment(context.sceptre_dir, environment_name)
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
    environment_name, _ = os.path.split(stack_name)
    env = Environment(context.sceptre_dir, environment_name)
    try:
        env.stacks[stack_name].launch()
    except Exception as e:
        context.error = e


@when('the user describes the resources of stack "{stack_name}"')
def step_impl(context, stack_name):
    environment_name, _ = os.path.split(stack_name)
    env = Environment(context.sceptre_dir, environment_name)

    context.output = env.stacks[stack_name].describe_resources()


@then('stack "{stack_name}" exists in "{desired_status}" state')
def step_impl(context, stack_name, desired_status):
    full_name = get_cloudformation_stack_name(context, stack_name)
    status = get_stack_status(context, full_name)
    assert (status == desired_status)


@then('stack "{stack_name}" does not exist')
def step_impl(context, stack_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    status = get_stack_status(context, full_name)
    assert (status is None)


@then('the resources of stack "{stack_name}" are described')
def step_impl(context, stack_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    response = retry_boto_call(
        context.client.describe_stack_resources,
        StackName=full_name
    )

    properties = {"LogicalResourceId", "PhysicalResourceId"}
    formatted_response = [
            {k: v for k, v in item.items() if k in properties}
            for item in response["StackResources"]
    ]

    assert formatted_response == context.output


def get_stack_status(context, stack_name):
    try:
        stack = retry_boto_call(context.cloudformation.Stack, stack_name)
        retry_boto_call(stack.load)
        return stack.stack_status
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError' \
          and e.response['Error']['Message'].endswith("does not exist"):
            return None
        else:
            raise e


def create_stack(context, stack_name, body, **kwargs):
    retry_boto_call(
        context.client.create_stack,
        StackName=stack_name, TemplateBody=body, **kwargs
    )

    wait_for_final_state(context, stack_name)


def update_stack(context, stack_name, body, **kwargs):
    stack = retry_boto_call(context.cloudformation.Stack, stack_name)
    retry_boto_call(stack.update, TemplateBody=body, **kwargs)

    wait_for_final_state(context, stack_name)


def delete_stack(context, stack_name):
    stack = retry_boto_call(context.cloudformation.Stack, stack_name)
    retry_boto_call(stack.delete)

    waiter = context.client.get_waiter('stack_delete_complete')
    waiter.config.delay = 4
    waiter.config.max_attempts = 240
    waiter.wait(StackName=stack_name)


def wait_for_final_state(context, stack_name):
    stack = retry_boto_call(context.cloudformation.Stack, stack_name)
    delay = 2
    max_retries = 150
    attempts = 0
    while attempts < max_retries:
        retry_boto_call(stack.load)
        if not stack.stack_status.endswith("IN_PROGRESS"):
            return
        attempts += 1
        time.sleep(delay)
    raise Exception("Timeout waiting for stack to reach final state.")
