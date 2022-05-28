import click
from colorama import Fore, Style

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions
from sceptre.cli.helpers import confirmation
from sceptre.cli.helpers import stack_status_exit_code
from sceptre.plan.plan import SceptrePlan
from sceptre.stack import LaunchAction


@click.command(name="launch", short_help="Launch a Stack or StackGroup.")
@click.argument("path")
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def launch_command(ctx, path, yes):
    """
    Launch a Stack or StackGroup for a given config PATH.
    \f

    :param path: The path to launch. Can be a Stack or StackGroup.
    :type path: str
    :param yes: A flag to answer 'yes' to all CLI questions.
    :type yes: bool
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    plan = SceptrePlan(context)

    stacks_to_exclude = []
    for stacks in plan.launch_order:
        for stack in stacks:
            if stack.launch_action == LaunchAction.exclude:
                stacks_to_exclude.append(stack)

    if stacks_to_exclude:
        delete_message = "The following stacks are excluded from the launch. They will be deleted, if they exist:\n"
        for stack in stacks_to_exclude:
            delete_message += f"{Fore.YELLOW}{stack.name}{Style.RESET_ALL}\n"

        print(delete_message)

    confirmation(plan.launch.__name__, yes, command_path=path)
    responses = plan.launch()
    exit(stack_status_exit_code(responses.values()))
