import click

from helpers import catch_exceptions, get_stack


@click.command(name="execute")
@click.argument("path")
@click.argument("change-set-name", required=False)
@click.pass_context
@catch_exceptions
def execute(ctx, path, change_set_name):
    """
    Executes a change set.

    """
    stack = get_stack(ctx, path)
    stack.execute_change_set(change_set_name)
