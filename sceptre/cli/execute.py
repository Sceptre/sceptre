import click

from sceptre.cli.helpers import catch_exceptions, confirmation
from sceptre.cli.helpers import get_stack_or_env


@click.command(name="execute")
@click.argument("path")
@click.argument("change-set-name", required=False)
@click.option(
    "-y", "--yes", is_flag=True, help="Assume yes to all questions."
)
@click.pass_context
@catch_exceptions
def execute_command(ctx, path, change_set_name, yes):
    """
    Executes a change set.

    """
    stack, _ = get_stack_or_env(ctx, path)
    confirmation("execute", yes, change_set=change_set_name, stack=path)
    stack.execute_change_set(change_set_name)
