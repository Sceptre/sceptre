from itertools import chain

import boto3
from behave import given, then
from behave.runner import Context

from sceptre.context import SceptreContext
from sceptre.plan.plan import SceptrePlan
from helpers import get_cloudformation_stack_name, retry_boto_call


@given('all files in template bucket for stack "{stack_name}" are deleted at cleanup')
def step_impl(context: Context, stack_name):
    """Add this as a given to ensure that the template bucket is cleaned up before we attempt to
    delete it; Otherwise, it will fail since you can't delete a bucket with objects in it.
    """
    context.add_cleanup(
        cleanup_template_files_in_bucket,
        context.sceptre_dir,
        stack_name
    )


@then('the template for stack "{stack_name}" has been uploaded')
def step_impl(context: Context, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir
    )
    plan = SceptrePlan(sceptre_context)
    buckets = get_template_buckets(plan)
    assert len(buckets) > 0
    filtered_objects = list(chain.from_iterable(
        bucket.objects.filter(
            Prefix=stack_name
        )
        for bucket in buckets
    ))

    assert len(filtered_objects) == len(plan.command_stacks)
    for stack in plan.command_stacks:
        for obj in filtered_objects:
            if obj.key.startswith(stack.name):
                s3_template = obj.get()['Body'].read().decode('utf-8')
                expected = stack.template.body
                assert s3_template == expected
                break
        else:
            assert False, "Could not found uploaded template"


@then('the stack "{resource_stack_name}" has a role defined by stack "{role_stack_name}"')
def step_impl(context, resource_stack_name, role_stack_name):
    role_stack_resources = get_stack_resources(context, role_stack_name)
    role_name = role_stack_resources[0]['PhysicalResourceId']
    resource_stack = describe_stack(context, resource_stack_name)
    found_role_arn = resource_stack['RoleARN']
    assert found_role_arn.endswith(role_name)


@then('the stack "{resource_stack_name}" has a notification defined by stack "{topic_stack_name}"')
def step_impl(context, resource_stack_name, topic_stack_name):
    topic_stack_resources = get_stack_resources(context, topic_stack_name)
    topic = topic_stack_resources[0]['PhysicalResourceId']
    resource_stack = describe_stack(context, resource_stack_name)
    notification_arns = resource_stack['NotificationARNs']
    assert topic in notification_arns


def cleanup_template_files_in_bucket(sceptre_dir, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=sceptre_dir
    )
    plan = SceptrePlan(sceptre_context)
    buckets = get_template_buckets(plan)
    for bucket in buckets:
        bucket.objects.delete()


def get_template_buckets(plan: SceptrePlan):
    s3_resource = boto3.resource('s3')
    return [
        s3_resource.Bucket(stack.template_bucket_name)
        for stack in plan.command_stacks
        if stack.template_bucket_name is not None
    ]


def get_stack_resources(context, stack_name):
    cf_stack_name = get_cloudformation_stack_name(context, stack_name)
    resources = retry_boto_call(
        context.client.describe_stack_resources,
        StackName=cf_stack_name
    )
    return resources['StackResources']


def describe_stack(context, stack_name):
    cf_stack_name = get_cloudformation_stack_name(context, stack_name)
    response = retry_boto_call(
        context.client.describe_stacks,
        StackName=cf_stack_name
    )
    return response['Stacks'][0]
