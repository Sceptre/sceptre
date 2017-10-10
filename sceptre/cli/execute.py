import click

from sceptre.cli.helpers import catch_exceptions, confirmation


@click.command(name="execute")
@click.argument("path")
@click.argument("change-set-name", required=False)
@click.option("-y", "--yes", is_flag=True)
@click.pass_context
@catch_exceptions
def execute_command(ctx, path, change_set_name, yes):
    """
    Executes a change set.

    """
    stack = ctx.obj["config_reader"].construct_stack(path)
    confirmation("execute", yes, change_set=change_set_name, stack=path)
    stack.execute_change_set(change_set_name)
