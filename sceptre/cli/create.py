import click

from sceptre.cli.helpers import catch_exceptions, confirmation
from sceptre.cli.helpers import get_stack_or_stack_group
from sceptre.stack_status import StackStatus
from sceptre.plan.plan import SceptrePlan


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
    action = "create"

    stack, _ = get_stack_or_stack_group(ctx, path)
    if change_set_name:
        confirmation(action, yes, change_set=change_set_name, stack=path)
        command = 'create_change_set'
        plan = SceptrePlan(path, command, stack)
        plan.execute(change_set_name)
    else:
        confirmation(action, yes, stack=path)
        plan = SceptrePlan(path, action, stack)
        response = plan.execute()
        if response != StackStatus.COMPLETE:
            exit(1)
