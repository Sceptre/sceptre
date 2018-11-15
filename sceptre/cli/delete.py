import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions
from sceptre.cli.helpers import confirmation
from sceptre.cli.helpers import stack_status_exit_code
from sceptre.plan.plan import SceptrePlan


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
    """
    context = SceptreContext(
        command_path=path,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options")
    )

    plan = SceptrePlan(context)

    if len(plan.stack_group.stacks) == 1:
        if change_set_name:
            confirmation(
                plan.delete_change_set.__name__,
                yes,
                change_set=change_set_name,
                stack=path
            )
            plan.delete_change_set(change_set_name)
        else:
            confirmation(plan.delete.__name__, yes, stack=path)
            plan.delete()
            exit(stack_status_exit_code(plan))
    elif plan.stack_group:
        confirmation(plan.delete.__name__, yes, stack_group=path)
        plan.delete()
        exit(stack_status_exit_code(plan))
