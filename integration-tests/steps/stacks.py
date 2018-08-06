from behave import *
import time
import os
import yaml
import boto3
from contextlib import contextmanager
from botocore.exceptions import ClientError
from helpers import read_template_file, get_cloudformation_stack_name
from helpers import retry_boto_call

from sceptre.config.reader import ConfigReader


def set_stack_timeout(context, stack_name, stack_timeout):
    config_path = os.path.join(
        context.sceptre_dir, "config", stack_name + ".yaml"
    )
    with open(config_path) as config_file:
        stack_config = yaml.safe_load(config_file)

    stack_config["stack_timeout"] = int(stack_timeout)

    with open(config_path, 'w') as config_file:
        yaml.safe_dump(stack_config, config_file, default_flow_style=False)


@given('stack "{stack_name}" does not exist')
def step_impl(context, stack_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    status = get_stack_status(context, full_name)
    if status is not None:
        delete_stack(context, full_name)
    status = get_stack_status(context, full_name)
    assert (status is None)


@given('stack "{stack_name}" does not exist in "{region_name}"')
def step_impl(context, stack_name, region_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    with region(region_name):
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


@given('the stack_timeout for stack "{stack_name}" is "{stack_timeout}"')
def step_impl(context, stack_name, stack_timeout):
    set_stack_timeout(context, stack_name, stack_timeout)


@when('the user creates stack "{stack_name}"')
def step_impl(context, stack_name):
    config_reader = ConfigReader(context.sceptre_dir)
    stack = config_reader.construct_stack(stack_name + ".yaml")
    try:
        stack.create()
    except ClientError as e:
        if e.response['Error']['Code'] == 'AlreadyExistsException' \
          and e.response['Error']['Message'].endswith("already exists"):
            return
        else:
            raise e


@when('the user updates stack "{stack_name}"')
def step_impl(context, stack_name):
    config_reader = ConfigReader(context.sceptre_dir)
    stack = config_reader.construct_stack(stack_name + ".yaml")
    try:
        stack.update()
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
    config_reader = ConfigReader(context.sceptre_dir)
    stack = config_reader.construct_stack(stack_name + ".yaml")
    try:
        stack.delete()
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationError' \
          and e.response['Error']['Message'].endswith("does not exist"):
            return
        else:
            raise e


@when('the user launches stack "{stack_name}"')
def step_impl(context, stack_name):
    config_reader = ConfigReader(context.sceptre_dir)
    stack = config_reader.construct_stack(stack_name + ".yaml")
    try:
        stack.launch()
    except Exception as e:
        context.error = e


@when('the user describes the resources of stack "{stack_name}"')
def step_impl(context, stack_name):
    config_reader = ConfigReader(context.sceptre_dir)
    stack = config_reader.construct_stack(stack_name + ".yaml")

    context.output = stack.describe_resources()


@then(
    'stack "{stack_name}" in "{region_name}" '
    'exists in "{desired_status}" state'
)
def step_impl(context, stack_name, region_name, desired_status):
    with region(region_name):
        full_name = get_cloudformation_stack_name(context, stack_name)
        status = get_stack_status(context, full_name, region_name)

        assert (status == desired_status)


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


def get_stack_status(context, stack_name, region_name=None):
    if region_name is not None:
        Stack = boto3.resource('cloudformation', region_name=region_name).Stack
    else:
        Stack = context.cloudformation.Stack

    try:
        stack = retry_boto_call(Stack, stack_name)
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


@contextmanager
def region(region_name):
    os.environ["AWS_REGION"] = region_name
    yield
    del os.environ["AWS_REGION"]


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
