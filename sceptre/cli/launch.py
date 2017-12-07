import click

from sceptre.cli.helpers import catch_exceptions, get_stack_or_env
from sceptre.cli.helpers import confirmation
from sceptre.stack_status import StackStatus


@click.command(name="launch")
@click.argument("path")
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def launch_command(ctx, path, yes):
    """
    Launch a stack or environment.

    Launch a stack or environment for a given config PATH.
    """
    action = "launch"

    stack, env = get_stack_or_env(ctx, path)

    if stack:
        confirmation(action, yes, stack=path)
        response = stack.launch()
        if response != StackStatus.COMPLETE:
            exit(1)
    elif env:
        confirmation(action, yes, environment=path)
        response = env.launch()
        if not all(
            status == StackStatus.COMPLETE for status in response.values()
        ):
            exit(1)
