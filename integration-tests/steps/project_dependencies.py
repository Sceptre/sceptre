from itertools import chain

import boto3
from behave import given, then
from behave.runner import Context

from sceptre.context import SceptreContext
from sceptre.plan.plan import SceptrePlan


@given('all files in template bucket for stack "{stack_name}" are deleted at cleanup')
def step_impl(context: Context, stack_name):

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
