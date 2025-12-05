import time
from pathlib import Path

from behave import *
from botocore.exceptions import ClientError

from helpers import read_template_file, get_cloudformation_stack_name, retry_boto_call
from sceptre.cli.launch import Launcher
from sceptre.cli.prune import PATH_FOR_WHOLE_PROJECT, Pruner
from sceptre.context import SceptreContext
from sceptre.diffing.diff_writer import DeepDiffWriter
from sceptre.diffing.stack_differ import DeepDiffStackDiffer, DifflibStackDiffer
from sceptre.helpers import sceptreise_path
from sceptre.plan.plan import SceptrePlan
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
    launch_stack_group(context, stack_group_name)


@when('the user launches stack_group "{stack_group_name}" with --prune')
def step_impl(context, stack_group_name):
    launch_stack_group(context, stack_group_name, True)


@when('the user launches stack_group "{stack_group_name}" with ignore dependencies')
def step_impl(context, stack_group_name):
    launch_stack_group(context, stack_group_name, False, True)


@when(
    'the user launches stack_group "{stack_group_name}" with max-concurrency {max_concurrency:d}'
)
def step_impl(context, stack_group_name, max_concurrency):
    launch_stack_group(context, stack_group_name, False, False, max_concurrency)


def launch_stack_group(
    context,
    stack_group_name,
    prune=False,
    ignore_dependencies=False,
    max_concurrency=None,
):
    sceptre_context = SceptreContext(
        command_path=stack_group_name,
        project_path=context.sceptre_dir,
        ignore_dependencies=ignore_dependencies,
        max_concurrency=max_concurrency,
    )

    launcher = Launcher(sceptre_context)

    # Patch the executor to capture the number of threads used
    from unittest.mock import patch
    from sceptre.plan.executor import SceptrePlanExecutor

    original_init = SceptrePlanExecutor.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        context.executor_num_threads = self.num_threads

    with patch.object(SceptrePlanExecutor, "__init__", patched_init):
        launcher.launch(prune)


@when('the user deletes stack_group "{stack_group_name}"')
def step_impl(context, stack_group_name):
    sceptre_context = SceptreContext(
        command_path=stack_group_name, project_path=context.sceptre_dir
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    sceptre_plan.delete()


@when('the user deletes stack_group "{stack_group_name}" with ignore dependencies')
def step_impl(context, stack_group_name):
    sceptre_context = SceptreContext(
        command_path=stack_group_name,
        project_path=context.sceptre_dir,
        ignore_dependencies=True,
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    sceptre_plan.delete()


@when(
    'the user describes resources in stack_group "{stack_group_name}" with ignore dependencies'
)
def step_impl(context, stack_group_name):
    sceptre_context = SceptreContext(
        command_path=stack_group_name,
        project_path=context.sceptre_dir,
        ignore_dependencies=True,
    )

    sceptre_plan = SceptrePlan(sceptre_context)
    context.response = sceptre_plan.describe_resources().values()


@then('all the stacks in stack_group "{stack_group_name}" are in "{status}"')
def step_impl(context, stack_group_name, status):
    full_stack_names = get_full_stack_names(context, stack_group_name).values()

    check_stack_status(context, full_stack_names, status)


@then(
    'only the stacks in stack_group "{stack_group_name}", excluding dependencies are in "{status}"'
)
def step_impl(context, stack_group_name, status):
    full_stack_names = get_full_stack_names(context, stack_group_name).values()

    check_stack_status(context, full_stack_names, status)


@then('all the stacks in stack_group "{stack_group_name}" do not exist')
def step_impl(context, stack_group_name):
    full_stack_names = get_full_stack_names(context, stack_group_name).values()

    check_stack_status(context, full_stack_names, None)


@then('stack "{stack_name}" is described as "{status}"')
def step_impl(context, stack_name, status):
    response = next(
        (stack for stack in context.response if stack_name in stack),
        {stack_name: "PENDING"},
    )

    assert response[stack_name] == status


@then('that stack "{first_stack}" was created before "{second_stack}"')
def step_impl(context, first_stack, second_stack):
    stacks = [
        get_cloudformation_stack_name(context, first_stack),
        get_cloudformation_stack_name(context, second_stack),
    ]
    creation_times = get_stack_creation_times(context, stacks)

    assert creation_times[stacks[0]] < creation_times[stacks[1]]


@then("the executor used {num_threads:d} thread")
@then("the executor used {num_threads:d} threads")
def step_impl(context, num_threads):
    assert hasattr(
        context, "executor_num_threads"
    ), "Executor thread count was not captured"
    assert (
        context.executor_num_threads == num_threads
    ), f"Expected {num_threads} threads but executor used {context.executor_num_threads}"


@then("the executor used at least {min_threads:d} thread")
@then("the executor used at least {min_threads:d} threads")
def step_impl(context, min_threads):
    assert hasattr(
        context, "executor_num_threads"
    ), "Executor thread count was not captured"
    assert (
        context.executor_num_threads >= min_threads
    ), f"Expected at least {min_threads} threads but executor used {context.executor_num_threads}"


@when('the user diffs stack group "{group_name}" with "{diff_type}"')
def step_impl(context, group_name, diff_type):
    sceptre_context = SceptreContext(
        command_path=group_name, project_path=context.sceptre_dir
    )
    sceptre_plan = SceptrePlan(sceptre_context)
    differ_classes = {"deepdiff": DeepDiffStackDiffer, "difflib": DifflibStackDiffer}
    writer_class = {"deepdiff": DeepDiffWriter, "difflib": DeepDiffWriter}

    differ = differ_classes[diff_type]()
    context.writer_class = writer_class[diff_type]
    context.output = list(sceptre_plan.diff(differ).values())


@when("the whole project is pruned")
def step_impl(context):
    sceptre_context = SceptreContext(
        command_path=PATH_FOR_WHOLE_PROJECT,
        project_path=context.sceptre_dir,
    )

    pruner = Pruner(sceptre_context)
    pruner.prune()


def get_stack_creation_times(context, stacks):
    creation_times = {}
    response = retry_boto_call(context.client.describe_stacks)
    for stack in response["Stacks"]:
        if stack["StackName"] in stacks:
            creation_times[stack["StackName"]] = stack["CreationTime"]
    return creation_times


def get_stack_names(context, stack_group_name):
    config_dir = Path(context.sceptre_dir) / "config"
    path = config_dir / stack_group_name

    stack_names = []

    for child in path.rglob("*"):
        if child.is_dir() or child.stem == "config":
            continue

        relative_path = child.relative_to(config_dir)
        stack_name = sceptreise_path(str(relative_path).replace(child.suffix, ""))
        stack_names.append(stack_name)

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
                context.client.create_stack, StackName=stack_name, TemplateBody=body
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "AlreadyExistsException" and e.response[
                "Error"
            ]["Message"].endswith("already exists"):
                pass
            else:
                raise e
    for stack_name in stack_names:
        wait_for_final_state(context, stack_name)


def delete_stacks(context, stack_names):
    waiter = context.client.get_waiter("stack_delete_complete")
    waiter.config.delay = 5
    waiter.config.max_attempts = 240

    for stack_name in reversed(list(stack_names)):
        time.sleep(1)
        stack = retry_boto_call(context.cloudformation.Stack, stack_name)
        retry_boto_call(stack.delete)
        waiter.wait(StackName=stack_name)
        time.sleep(1)


def check_stack_status(context, stack_names, desired_status):
    response = retry_boto_call(context.client.describe_stacks)

    for stack_name in stack_names:
        for stack in response["Stacks"]:
            if stack["StackName"] == stack_name:
                assert stack["StackStatus"] == desired_status
