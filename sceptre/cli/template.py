import click

from helpers import catch_exceptions, get_stack, write


@click.command(name="validate")
@click.argument("path")
@click.pass_context
@catch_exceptions
def validate(ctx, path):
    """
    Validates the template.

    Validates the template used for stack in PATH.
    """
    stack = get_stack(ctx, path)
    write(stack.template.validate(), ctx.obj["output_format"])


@click.command(name="generate")
@click.argument("path")
@click.pass_context
@catch_exceptions
def generate(ctx, path):
    """
    Prints the template.

    Prints the template used for stack in PATH.
    """
    stack = get_stack(ctx, path)
    write(stack.template.body)
