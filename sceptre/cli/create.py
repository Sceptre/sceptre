import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions, confirmation
from sceptre.plan.plan import SceptrePlan
from sceptre.cli.helpers import stack_status_exit_code


@click.command(name="create", short_help="Creates a stack or a change set.")
@click.argument("path")
@click.argument("change-set-name", required=False)
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def create_command(ctx, path, change_set_name, yes):
    """
    Creates a stack for a given config PATH. Or if CHANGE_SET_NAME is specified
    creates a change set for stack in PATH.
    \f

    :param path: Path to a Stack or StackGroup
    :type path: str
    :param change_set_name: A name of the Change Set - optional
    :type change_set_name: str
    :param yes: A flag to assume yes to all questions.
    :type yes: bool
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies")
    )

    action = "create"
    plan = SceptrePlan(context)

    if change_set_name:
        confirmation(action, yes, change_set=change_set_name,
                     command_path=path)
        plan.create_change_set(change_set_name)
    else:
        confirmation(action, yes, command_path=path)
        responses = plan.create()
        exit(stack_status_exit_code(responses.values()))
