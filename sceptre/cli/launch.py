import logging

import click
from click import Context
from colorama import Fore, Style

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions
from sceptre.cli.helpers import confirmation
from sceptre.cli.helpers import stack_status_exit_code
from sceptre.exceptions import StackDependencyCannotBeLaunchedError
from sceptre.plan.plan import SceptrePlan
from sceptre.stack import LaunchAction, Stack

logger = logging.getLogger(__name__)


@click.command(name="launch", short_help="Launch a Stack or StackGroup.")
@click.argument("path")
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def launch_command(ctx: Context, path: str, yes: bool):
    """
    Launch a Stack or StackGroup for a given config PATH. This command is intended as a catch-all
    command that will apply any changes from Stack Configs indicated via the path.

    \b
    * Any Stacks that do not exist will be created
    * Any stacks that already exist will be updated (if there are any changes)
    * If any stacks are marked with launch_type: exclude, they will NOT be created and, if they exist,
    will be deleted.

    \f

    :param path: The path to launch. Can be a Stack or StackGroup.
    :param yes: A flag to answer 'yes' to all CLI questions.
    """
    deploy_context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )
    delete_context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=True,
        full_scan=True
    )

    plan = SceptrePlan(deploy_context)
    plan.resolve(plan.launch.__name__)

    stacks_to_remove = []
    stacks_to_skip = []
    for i, batch in enumerate(plan.launch_order):
        for stack in batch:
            if stack.launch_action == LaunchAction.remove:
                stacks_to_remove.append(stack)
            elif stack.launch_action == LaunchAction.skip:
                stacks_to_skip.append((i, stack))
            elif is_any_stack_dependency_removed_from_launch(stack):
                raise StackDependencyCannotBeLaunchedError()

    if stacks_to_skip:
        skip_message = "The following stacks will be skipped; They will be neither created nor deleted:\n"
        for batch_index, stack in stacks_to_skip:
            skip_message += f"{Fore.YELLOW}{stack.name}{Style.RESET_ALL}\n"
            plan.launch_order[batch_index].remove(stack)

        print(skip_message)

    if stacks_to_remove:
        delete_context = SceptreContext(
            command_path=path,
            project_path=ctx.obj.get("project_path"),
            user_variables=ctx.obj.get("user_variables"),
            options=ctx.obj.get("options"),
            ignore_dependencies=True,
            full_scan=True
        )
        deletion_plan = SceptrePlan(delete_context)
        deletion_plan.command_stacks = set(stacks_to_remove)

        delete_message = "The following stacks will be excluded from the launch launch. They will be deleted, if they exist:\n"
        for stack in stacks_to_remove:
            delete_message += f"{Fore.YELLOW}{stack.name}{Style.RESET_ALL}\n"

        print(delete_message)

    confirmation(plan.launch.__name__, yes, command_path=path)

    if stacks_to_remove:
        deletions = deletion_plan.delete()
        exit_code = stack_status_exit_code(deletions)
        if exit_code != 0:
            exit(exit_code)

    responses = plan.launch()
    exit(stack_status_exit_code(responses.values()))


def is_any_stack_dependency_removed_from_launch(stack: Stack) -> bool:
    for dependency in stack.dependencies:
        dependency: Stack
        if dependency.launch_action == LaunchAction.remove:
            logger.error(
                f"Stack {stack.name} depends on stack {dependency.name}, which has a launch "
                f"action of remove. Cannot launch stack {stack.name}"
            )
            return True
        if is_any_stack_dependency_removed_from_launch(dependency):
            return True

    return False
