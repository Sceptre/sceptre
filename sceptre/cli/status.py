import click

from sceptre.cli.helpers import catch_exceptions, get_stack_or_env, write


@click.command(name="status")
@click.argument("path")
@click.pass_context
@catch_exceptions
def status_command(ctx, path):
    """
    Print status of stack or environment.

    Prints the stack status or the status of the stacks within a environment
    for a given config PATH.
    """
    output_format = ctx.obj["output_format"]
    no_colour = ctx.obj["no_colour"]

    stack, env = get_stack_or_env(ctx, path)

    if stack:
        write(stack.get_status(), no_colour=no_colour)
    elif env:
        write(env.describe(), output_format=output_format, no_colour=no_colour)
