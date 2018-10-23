from behave import *
import os
import time
from sceptre.config.reader import ConfigReader
from botocore.exceptions import ClientError
from helpers import read_template_file, get_cloudformation_stack_name
from helpers import retry_boto_call
from stacks import wait_for_final_state
from templates import set_template_path


@given('stack_group "{stack_group_name}" does not exist')
def step_impl(context, stack_group_name):
    full_stack_names = get_full_stack_names(context, stack_group_name).values()

    delete_stacks(context, full_stack_names)

    check_stack_status(context, full_stack_names, None)


@given('all the stacks in stack_group "{stack_group_name}" are in "{status}"')
def step_impl(context, stack_group_name, status):
    full_stack_names = get_full_stack_names(context, stack_group_name).values()

    response = retry_boto_call(context.client.describe_stacks)

    stacks_to_delete = []

    for stack_name in full_stack_names:
        for stack in response["Stacks"]:
            if stack["StackName"] == stack_name:
                if stack["StackStatus"] != status:
                    stacks_to_delete.append(stack_name)

    delete_stacks(context, stacks_to_delete)

    for stack in get_stack_names(context, stack_group_name):
        set_template_path(context, stack, "valid_template.json")
    create_stacks(context, full_stack_names)

    check_stack_status(context, full_stack_names, status)


@when('the user launches stack_group "{stack_group_name}"')
def step_impl(context, stack_group_name):
    stack_group = ConfigReader(context.sceptre_dir).construct_stack_group(stack_group_name)
    stack_group.launch()


@when('the user deletes stack_group "{stack_group_name}"')
def step_impl(context, stack_group_name):
    stack_group = ConfigReader(context.sceptre_dir).construct_stack_group(stack_group_name)
    stack_group.delete()


@when('the user describes stack_group "{stack_group_name}"')
def step_impl(context, stack_group_name):
    stack_group = ConfigReader(context.sceptre_dir).construct_stack_group(stack_group_name)
    context.response = stack_group.describe()


@when('the user describes resources in stack_group "{stack_group_name}"')
def step_impl(context, stack_group_name):
    stack_group = ConfigReader(context.sceptre_dir).construct_stack_group(stack_group_name)
    context.response = stack_group.describe_resources()


@then('all the stacks in stack_group "{stack_group_name}" are in "{status}"')
def step_impl(context, stack_group_name, status):
    full_stack_names = get_full_stack_names(context, stack_group_name).values()

    check_stack_status(context, full_stack_names, status)


@then('all the stacks in stack_group "{stack_group_name}" do not exist')
def step_impl(context, stack_group_name):
    full_stack_names = get_full_stack_names(context, stack_group_name).values()

    check_stack_status(context, full_stack_names, None)


@then('all stacks in stack_group "{stack_group_name}" are described as "{status}"')
def step_impl(context, stack_group_name, status):
    stacks_names = get_stack_names(context, stack_group_name)
    expected_response = {stack_name: status for stack_name in stacks_names}
    assert context.response == expected_response


@then('no resources are described')
def step_impl(context):
    assert context.response == {}


@then('stack "{stack_name}" is described as "{status}"')
def step_impl(context, stack_name, status):
    assert context.response[stack_name] == status


@then('only all resources in stack_group "{stack_group_name}" are described')
def step_impl(context, stack_group_name):
    stacks_names = get_full_stack_names(context, stack_group_name)
    expected_resources = {}
    sceptre_response = []
    for stack_resources in context.response.values():
        for resource in stack_resources:
            sceptre_response.append(resource["PhysicalResourceId"])

    for short_name, full_name in stacks_names.items():
        time.sleep(1)
        response = retry_boto_call(
            context.client.describe_stack_resources,
            StackName=full_name
        )
        expected_resources[short_name] = response["StackResources"]

    for short_name, resources in expected_resources.items():
        for resource in resources:
            sceptre_response.remove(resource["PhysicalResourceId"])

    assert sceptre_response == []


@then('only resources in stack "{stack_name}" are described')
def step_impl(context, stack_name):
    expected_resources = {}
    sceptre_response = []
    for stack_resources in context.response.values():
        for resource in stack_resources:
            sceptre_response.append(resource["PhysicalResourceId"])

    response = retry_boto_call(
        context.client.describe_stack_resources,
        StackName=get_cloudformation_stack_name(context, stack_name)
    )
    expected_resources[stack_name] = response["StackResources"]

    for short_name, resources in expected_resources.items():
        for resource in resources:
            sceptre_response.remove(resource["PhysicalResourceId"])

    assert sceptre_response == []


@then('that stack "{first_stack}" was created before "{second_stack}"')
def step_impl(context, first_stack, second_stack):
    stacks = [
        get_cloudformation_stack_name(context, first_stack),
        get_cloudformation_stack_name(context, second_stack)
    ]
    creation_times = get_stack_creation_times(context, stacks)

    assert creation_times[stacks[0]] < creation_times[stacks[1]]


def get_stack_creation_times(context, stacks):
    creation_times = {}
    response = retry_boto_call(context.client.describe_stacks)
    for stack in response["Stacks"]:
        if stack["StackName"] in stacks:
            creation_times[stack["StackName"]] = stack["CreationTime"]
    return creation_times


def get_stack_names(context, stack_group_name):
    path = os.path.join(context.sceptre_dir, "config", stack_group_name)
    stack_names = []
    for root, dirs, files in os.walk(path):
        for filepath in files:
            filename = os.path.splitext(filepath)[0]
            if not filename == "config":
                prefix = stack_group_name
                stack_group = root[path.find(prefix):]
                stack_names.append(os.path.join(stack_group, filename))
    return stack_names


def get_full_stack_names(context, stack_group_name):
    stack_names = get_stack_names(context, stack_group_name)

    return {
        stack_name: get_cloudformation_stack_name(context, stack_name)
        for stack_name in stack_names
    }


def create_stacks(context, stack_names):
    body = read_template_file(context, "valid_template.json")
    for stack_name in stack_names:
        time.sleep(1)
        try:
            retry_boto_call(
                context.client.create_stack,
                StackName=stack_name,
                TemplateBody=body
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException' \
              and e.response['Error']['Message'].endswith("already exists"):
                pass
            else:
                raise e
    for stack_name in stack_names:
        wait_for_final_state(context, stack_name)


def delete_stacks(context, stack_names):
    for stack_name in stack_names:
        time.sleep(1)
        stack = retry_boto_call(context.cloudformation.Stack, stack_name)
        retry_boto_call(stack.delete)

    waiter = context.client.get_waiter('stack_delete_complete')
    waiter.config.delay = 5
    waiter.config.max_attempts = 240
    for stack_name in stack_names:
        time.sleep(1)
        waiter.wait(StackName=stack_name)


def check_stack_status(context, stack_names, desired_status):
    response = retry_boto_call(context.client.describe_stacks)

    for stack_name in stack_names:
        for stack in response["Stacks"]:
            if stack["StackName"] == stack_name:
                assert stack["StackStatus"] == desired_status
