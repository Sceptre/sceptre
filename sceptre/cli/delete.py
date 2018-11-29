import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions
from sceptre.cli.helpers import confirmation
from sceptre.cli.helpers import stack_status_exit_code
from sceptre.plan.plan import SceptrePlan

from colorama import Fore, Style


@click.command(name="delete")
@click.argument("path")
@click.argument("change-set-name", required=False)
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def delete_command(ctx, path, change_set_name, yes):
    """
    Deletes a stack or a change set.

    Deletes a stack for a given config PATH. Or if CHANGE_SET_NAME is specified
    deletes a change set for stack in PATH.

    :param path: Path to execute command on.
    :type path: str
    :param change_set_name: The name of the change set to use - optional
    :type change_set_name: str
    :param yes: Flag to answer yes to all CLI questions.
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
    plan.resolve(command='delete', reverse=True)

    dependencies = ''
    for stacks in plan.launch_order:
        for stack in stacks:
            dependencies += "{}{}{}\n".format(Fore.YELLOW, stack.name, Style.RESET_ALL)

    print("The following stacks in the following order will be deleted:\n{}".format(dependencies))

    confirmation(
        plan.delete_change_set.__name__,
        yes,
        change_set=change_set_name,
        command_path=path
    )
    if change_set_name:
        plan.delete_change_set(change_set_name)
    else:
        responses = plan.delete()
        exit(stack_status_exit_code(responses.values()))
