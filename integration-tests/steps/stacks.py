from behave import *
import os
import boto3
from botocore.exceptions import ClientError
from sceptre.environment import Environment


def before_all(context):
    context.cloudformation = boto3.resource('cloudformation')
    contex.client = boto3.client("cloudformation")
    context.sceptre_dir = os.path.join(
        os.getcwd(), "integration-tests", "sceptre-project"
    )
    context.default_environment = "default"


@given('stack "{stack_name}" does not exist')
def step_impl(context, stack_name):
    status = get_stack_status(context, state_name)
    assert (status is None)


@given('stack "{stack_name}" exists in "{state}" state')
def step_impl(context, stack_name, state):
    status = get_stack_status(context, stack_name)
    if status != state:
        delete_stack(context, stack_name)
        create_stack(context, stack_name)
    elif status is None:
        create_stack(context, stack_name)

    status = get_stack_status(context, stack_name)
    assert (status == state)


@when('the user creates stack "{stack_name}"')
def step_impl(context, stack_name):
    env = Environment(context.sceptre_dir, context.default_environment)
    env.stacks[stack_name].create()


@then('stack "{stack_name}" exists in "{state}" state')
def step_impl(context, stack_name, state):
    status = get_stack_status(context, state_name)
    assert (status == state)

def get_stack_status(context, stack_name):
    name = "-".join(
        [sceptre-integration-tests, context.default_environment, stack_name]
    )
    try:
        stack = context.cloudformation.Stack(name)
        stack.load()
    except ClientError as e:
        if e.response['Error']['Code'] == 'AmazonCloudFormationException':
            return None
        else:
            raise e
    return stack.stack_status


def create_stack(context, stack_name):
    path = os.path.join(
        context.sceptre_dir, context.default_environment, stack_name + ".yaml"
    )

    name = "-".join(
        [sceptre-integration-tests, context.default_environment, stack_name]
    )

    with open(path) as template:
        body = template.read()

    response = context.client.create_stack(StackName=name, TemplateBody=body)

    waiter = context.client.get_waiter('stack_create_complete')
    waiter.config.delay = 2
    waiter.wait(StackName=name)


def delete_stack(context, stack_name):
    name = "-".join(
        [sceptre-integration-tests, context.default_environment, stack_name]
    )
    stack = context.cloudformation.Stack(name)

    waiter = context.client.get_waiter('stack_delete_complete')
    waiter.config.delay = 2
    waiter.wait(StackName=name)
