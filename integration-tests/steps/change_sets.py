from behave import *
import time

from sceptre.environment import Environment
from botocore.exceptions import ClientError
from helpers import read_template_file


def wait_for_final_state(context, stack_name, change_set_name):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    delay = 1
    max_retries = 10
    attempts = 0
    while attempts < max_retries:
        status = get_change_set_status(context, full_name, change_set_name)
        if status is None or ("IN_PROGRESS" not in status and "PENDING" not in status):
            return
        time.sleep(delay)
        attempts = attempts + 1
    raise Exception("Timeout waiting for change set to reach final state.")


@given(
    'stack "{stack_name}" has change set "{change_set_name}" using {filename}'
)
def step_impl(context, stack_name, change_set_name, filename):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    context.client.create_change_set(
        StackName=full_name,
        ChangeSetName=change_set_name,
        TemplateBody=read_template_file(context, filename)
    )
    wait_for_final_state(context, stack_name, change_set_name)


@given('stack "{stack_name}" does not have change set "{change_set_name}"')
def step_impl(context, stack_name, change_set_name):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    context.client.delete_change_set(
        ChangeSetName=change_set_name,
        StackName=full_name
    )


@when(
    'the user creates change set "{change_set_name}" for stack "{stack_name}"'
)
def step_impl(context, change_set_name, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)
    stack = env.stacks[stack_name]
    try:
        stack.create_change_set(change_set_name)
    except ClientError as e:
        if e.response['Error']['Code'] in {'ValidationError', 'ChangeSetNotFound'}:
            context.error = e
            return
        else:
            raise e
    wait_for_final_state(context, stack_name, change_set_name)


@when(
    'the user deletes change set "{change_set_name}" for stack "{stack_name}"'
)
def step_impl(context, change_set_name, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)
    stack = env.stacks[stack_name]
    try:
        stack.delete_change_set(change_set_name)
    except ClientError as e:
        if e.response['Error']['Code'] in {'ValidationError', 'ChangeSetNotFound'}:
            context.error = e
            return
        else:
            raise e
    # wait_for_final_state(context, stack_name, change_set_name)


@then(
    'stack "{stack_name}" has change set "{change_set_name}" in "{state}" state'
)
def step_impl(context, stack_name, change_set_name, state):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    response = context.client.describe_change_set(
        ChangeSetName=change_set_name,
        StackName=full_name
    )
    assert response.get("Status") == state


@then(
    'stack "{stack_name}" does not have change set "{change_set_name}"'
)
def step_impl(context, stack_name, change_set_name):
    full_name = "-".join(
        ["sceptre-integration-tests", context.default_environment, stack_name]
    )
    status = get_change_set_status(context, full_name, change_set_name)

    assert status is None


def get_change_set_status(context, stack_name, change_set_name):
    try:
        response = context.client.describe_change_set(
            ChangeSetName=change_set_name,
            StackName=stack_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ChangeSetNotFound':
            return None
        else:
            raise e
    return response["Status"]
