import boto3
from behave import given
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


def cleanup_template_files_in_bucket(sceptre_dir, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=sceptre_dir
    )
    plan = SceptrePlan(sceptre_context)
    s3_resource = boto3.resource('s3')
    for stack in plan.command_stacks:
        bucket = s3_resource.Bucket(stack.template_bucket_name)
        bucket.objects.delete()
