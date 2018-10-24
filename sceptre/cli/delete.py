import click

from sceptre.cli.helpers import catch_exceptions, get_stack_or_stack_group
from sceptre.cli.helpers import confirmation
from sceptre.stack_status import StackStatus
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
    action = "delete"

    stack, stack_group = get_stack_or_stack_group(ctx, path)

    if stack:
        if change_set_name:
            confirmation(action, yes, change_set=change_set_name, stack=path)
            command = 'delete_change_set'
            plan = SceptrePlan(path, command, stack)
            plan.execute(change_set_name)
        else:
            confirmation(action, yes, stack=path)
            plan = SceptrePlan(path, action, stack)
            response = plan.execute()
            if response != StackStatus.COMPLETE:
                exit(1)
    elif stack_group:
        confirmation(action, yes, stack_group=path)
        plan = SceptrePlan(path, action, stack_group)
        response = plan.execute()
        if not all(
            status == StackStatus.COMPLETE for status in response.values()
        ):
            exit(1)
