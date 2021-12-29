from behave import *
from helpers import get_cloudformation_stack_name

import boto3

from sceptre.plan.plan import SceptrePlan
from sceptre.context import SceptreContext


@given('a stack setting in stack "{stack_name}" has drifted')
def step_impl(context, stack_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    log_group_name = _get_output("LogGroup", full_name)
    client = boto3.client("logs")
    client.put_retention_policy(
        logGroupName=log_group_name,
        retentionInDays=7
    )


def _get_output(output_name, stack_name):
    client = boto3.client("cloudformation")
    response = client.describe_stacks(StackName=stack_name)
    key_name = stack_name + "-" + output_name
    for output in response["Stacks"][0]["Outputs"]:
        if output["OutputKey"] == output_name:
            return output["OutputValue"]


@when('the user detects drift on stack "{stack_name}"')
def step_impl(context, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir
    )
    sceptre_plan = SceptrePlan(sceptre_context)
    values = sceptre_plan.drift_detect().values()
    context.output = list(values)


@when('the user shows drift on stack "{stack_name}"')
def step_impl(context, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir
    )
    sceptre_plan = SceptrePlan(sceptre_context)
    values = sceptre_plan.drift_show().values()
    context.output = list(values)


@when('the user detects drift on stack_group "{stack_group_name}"')
def step_impl(context, stack_group_name):
    sceptre_context = SceptreContext(
        command_path=stack_group_name,
        project_path=context.sceptre_dir
    )
    sceptre_plan = SceptrePlan(sceptre_context)
    values = sceptre_plan.drift_detect().values()
    context.output = list(values)


@then('stack drift status is "{desired_status}"')
def step_impl(context, desired_status):
    assert context.output[0]["StackDriftStatus"] == desired_status


@then('stack resource drift status is "{desired_status}"')
def step_impl(context, desired_status):
    assert context.output[0][1]["StackResourceDrifts"][0]["StackResourceDriftStatus"] == desired_status


@then('stack_group drift statuses are each one of "{statuses}"')
def step_impl(context, statuses):
    status_list = [status.strip() for status in statuses.split(",")]
    for output in context.output:
        assert output["StackDriftStatus"] in status_list
