import click

from helpers import catch_exceptions, get_stack_and_env
from sceptre.stack_status import StackStatus


@click.command(name="launch")
@click.argument("path")
@click.option("-r", "--recursive", is_flag=True)
@click.pass_context
@catch_exceptions
def launch(ctx, path, recursive):
    """
    Launch a stack or environment.

    Launch a stack or environment for a given config PATH.
    """
    stack, env = get_stack_and_env(ctx, path, recursive)

    if stack:
        response = stack.launch()
        if response != StackStatus.COMPLETE:
            exit(1)
    else:
        response = env.launch()
        if not all(
            status == StackStatus.COMPLETE for status in response.values()
        ):
            exit(1)
