from behave import *
import time

from sceptre.plan.plan import SceptrePlan
from sceptre.context import SceptreContext
from botocore.exceptions import ClientError
from helpers import read_template_file, get_cloudformation_stack_name
from helpers import retry_boto_call


@given(
    'stack "{stack_name}" has change set "{change_set_name}" using "{filename}"'
)
def step_impl(context, stack_name, change_set_name, filename):
    full_name = get_cloudformation_stack_name(context, stack_name)
    retry_boto_call(
        context.client.create_change_set,
        StackName=full_name,
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'],
        ChangeSetName=change_set_name,
        TemplateBody=read_template_file(context, filename)
    )
    wait_for_final_state(context, stack_name, change_set_name)


@given('stack "{stack_name}" does not have change set "{change_set_name}"')
def step_impl(context, stack_name, change_set_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    retry_boto_call(
        context.client.delete_change_set,
        ChangeSetName=change_set_name,
        StackName=full_name
    )


@given('stack "{stack_name}" has no change sets')
def step_impl(context, stack_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    response = retry_boto_call(
        context.client.list_change_sets, StackName=full_name
    )
    for change_set in response["Summaries"]:
        time.sleep(1)
        retry_boto_call(
            context.client.delete_change_set,
            ChangeSetName=change_set['ChangeSetName'],
            StackName=full_name
        )


@when('the user creates change set "{change_set_name}" for stack "{stack_name}"')
def step_impl(context, change_set_name, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    allowed_errors = {'ValidationError', 'ChangeSetNotFound'}
    try:
        sceptre_plan.create_change_set(change_set_name)
    except ClientError as e:
        if e.response['Error']['Code'] in allowed_errors:
            context.error = e
            return
        else:
            raise e

    wait_for_final_state(context, stack_name, change_set_name)


@when('the user creates change set "{change_set_name}" for stack "{stack_name}" with ignore dependencies')
def step_impl(context, change_set_name, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir,
        ignore_dependencies=True
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    allowed_errors = {'ValidationError', 'ChangeSetNotFound'}
    try:
        sceptre_plan.create_change_set(change_set_name)
    except ClientError as e:
        if e.response['Error']['Code'] in allowed_errors:
            context.error = e
            return
        else:
            raise e

    wait_for_final_state(context, stack_name, change_set_name)


@when('the user deletes change set "{change_set_name}" for stack "{stack_name}"')
def step_impl(context, change_set_name, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    allowed_errors = {'ValidationError', 'ChangeSetNotFound'}
    sceptre_plan.delete_change_set(change_set_name)

    try:
        sceptre_plan.delete_change_set(change_set_name)
    except ClientError as e:
        if e.response['Error']['Code'] in allowed_errors:
            context.error = e
            return
        else:
            raise e


@when('the user deletes change set "{change_set_name}" for stack "{stack_name}" with ignore dependencies')
def step_impl(context, change_set_name, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir,
        ignore_dependencies=True
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    allowed_errors = {'ValidationError', 'ChangeSetNotFound'}
    sceptre_plan.delete_change_set(change_set_name)

    try:
        sceptre_plan.delete_change_set(change_set_name)
    except ClientError as e:
        if e.response['Error']['Code'] in allowed_errors:
            context.error = e
            return
        else:
            raise e


@when('the user lists change sets for stack "{stack_name}"')
def step_impl(context, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    allowed_errors = {'ValidationError', 'ChangeSetNotFound'}

    try:
        context.output = sceptre_plan.list_change_sets().values()
    except ClientError as e:
        if e.response['Error']['Code'] in allowed_errors:
            context.error = e
            return
        raise e


@when('the user lists change sets for stack "{stack_name}" with ignore dependencies')
def step_impl(context, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir,
        ignore_dependencies=True
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    allowed_errors = {'ValidationError', 'ChangeSetNotFound'}

    try:
        context.output = sceptre_plan.list_change_sets().values()
    except ClientError as e:
        if e.response['Error']['Code'] in allowed_errors:
            context.error = e
            return
        raise e


@when('the user executes change set "{change_set_name}" for stack "{stack_name}"')
def step_impl(context, change_set_name, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    allowed_errors = {'ValidationError', 'ChangeSetNotFound'}

    try:
        sceptre_plan.execute_change_set(change_set_name)
    except ClientError as e:
        if e.response['Error']['Code'] in allowed_errors:
            context.error = e
            return
        else:
            raise e


@when('the user executes change set "{change_set_name}" for stack "{stack_name}" with ignore dependencies')
def step_impl(context, change_set_name, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir,
        ignore_dependencies=True
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    allowed_errors = {'ValidationError', 'ChangeSetNotFound'}

    try:
        sceptre_plan.execute_change_set(change_set_name)
    except ClientError as e:
        if e.response['Error']['Code'] in allowed_errors:
            context.error = e
            return
        else:
            raise e


@when('the user describes change set "{change_set_name}" for stack "{stack_name}"')
def step_impl(context, change_set_name, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    allowed_errors = {'ValidationError', 'ChangeSetNotFound'}

    try:
        responses = sceptre_plan.describe_change_set(change_set_name)
    except ClientError as e:
        if e.response['Error']['Code'] in allowed_errors:
            context.error = e
            return
        else:
            raise e
    context.output = responses


@when('the user describes change set "{change_set_name}" for stack "{stack_name}" with ignore dependencies')
def step_impl(context, change_set_name, stack_name):
    sceptre_context = SceptreContext(
        command_path=stack_name + '.yaml',
        project_path=context.sceptre_dir,
        ignore_dependencies=True
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    allowed_errors = {'ValidationError', 'ChangeSetNotFound'}

    try:
        responses = sceptre_plan.describe_change_set(change_set_name)
    except ClientError as e:
        if e.response['Error']['Code'] in allowed_errors:
            context.error = e
            return
        else:
            raise e
    context.output = responses


@then('stack "{stack_name}" has change set "{change_set_name}" in "{state}" state')
def step_impl(context, stack_name, change_set_name, state):
    full_name = get_cloudformation_stack_name(context, stack_name)

    status = get_change_set_status(context, full_name, change_set_name)

    assert status == state


@then('stack "{stack_name}" does not have change set "{change_set_name}"')
def step_impl(context, stack_name, change_set_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    status = get_change_set_status(context, full_name, change_set_name)

    assert status is None


@then('the change sets for stack "{stack_name}" are listed')
def step_impl(context, stack_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    response = retry_boto_call(
        context.client.list_change_sets,
        StackName=full_name
    )
    for output in context.output:
        assert output == {stack_name: response.get("Summaries", {})}


@then('no change sets for stack "{stack_name}" are listed')
def step_impl(context, stack_name):
    for output in context.output:
        assert output == {stack_name: []}


@then('change set "{change_set_name}" for stack "{stack_name}" is described')
def step_impl(context, change_set_name, stack_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    response = retry_boto_call(
        context.client.describe_change_set,
        StackName=full_name,
        ChangeSetName=change_set_name
    )

    del response["ResponseMetadata"]
    for stack, output in context.output.items():
        del output["ResponseMetadata"]

    for stack, output in context.output.items():
        assert response == output


@then('stack "{stack_name}" was updated with change set "{change_set_name}"')
def step_impl(context, stack_name, change_set_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    response = retry_boto_call(
        context.client.describe_stacks,
        StackName=full_name
    )

    change_set_id = response["Stacks"][0]["ChangeSetId"]
    stack_status = response["Stacks"][0]["StackStatus"]

    assert stack_status == "UPDATE_COMPLETE"
    assert change_set_name == change_set_id.split("/")[1]


def get_change_set_status(context, stack_name, change_set_name):
    try:
        response = retry_boto_call(
            context.client.describe_change_set,
            ChangeSetName=change_set_name,
            StackName=stack_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ChangeSetNotFound':
            return None
        else:
            raise e
    return response["Status"]


def wait_for_final_state(context, stack_name, change_set_name):
    full_name = get_cloudformation_stack_name(context, stack_name)
    delay = 1
    max_retries = 10
    attempts = 0
    while attempts < max_retries:
        status = get_change_set_status(context, full_name, change_set_name)
        in_progress = "IN_PROGRESS" not in status and "PENDING" not in status
        if status is None or in_progress:
            return
        time.sleep(delay)
        attempts += 1
    raise Exception("Timeout waiting for change set to reach final state.")
