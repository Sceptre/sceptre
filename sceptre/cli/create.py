import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions, confirmation
from sceptre.plan.plan import SceptrePlan
from sceptre.cli.helpers import stack_status_exit_code


@click.command(name="create")
@click.argument("path")
@click.argument("change-set-name", required=False)
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def create_command(ctx, path, change_set_name, yes):
    """
    Creates a stack or a change set.

    Creates a stack for a given config PATH. Or if CHANGE_SET_NAME is specified
    creates a change set for stack in PATH.
    """
    context = SceptreContext(
                command_path=path,
                project_path=ctx.obj.get("project_path"),
                user_variables=ctx.obj.get("user_variables"),
                options=ctx.obj.get("options")
            )

    action = "create"
    plan = SceptrePlan(context)

    # TODO this isn't going to work with sub-stack-group-stacks
    if any(change_set_name for change_set_name in plan.stack_group.stacks):
        confirmation(action, yes, change_set=change_set_name, stack=path)
        plan.create_change_set(change_set_name)
    else:
        confirmation(action, yes, stack=path)
        plan.create()
        exit(stack_status_exit_code(plan))
