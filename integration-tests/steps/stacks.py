from behave import *
import json
import time
import os
import boto3
from botocore.exceptions import ClientError, WaiterError
from sceptre.environment import Environment
from helpers import read_template_file


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
