import click

from sceptre.cli.helpers import catch_exceptions, get_stack_or_env
from sceptre.cli.helpers import confirmation
from sceptre.stack_status import StackStatus


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

    stack, env = get_stack_or_env(ctx, path)

    if stack:
        if change_set_name:
            confirmation(action, yes, change_set=change_set_name, stack=path)
            stack.delete_change_set(change_set_name)
        else:
            confirmation(action, yes, stack=path)
            response = stack.delete()
            if response != StackStatus.COMPLETE:
                exit(1)
    elif env:
        confirmation(action, yes, environment=path)
        response = env.delete()
        if not all(
            status == StackStatus.COMPLETE for status in response.values()
        ):
            exit(1)
