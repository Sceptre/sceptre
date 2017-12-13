import click

from sceptre.cli.helpers import catch_exceptions, get_stack, write


@click.command(name="validate")
@click.argument("path")
@click.pass_context
@catch_exceptions
def validate_command(ctx, path):
    """
    Validates the template.

    Validates the template used for stack in PATH.
    """
    stack = get_stack(ctx, path)
    response = stack.template.validate()
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        del response['ResponseMetadata']
        click.echo("Template is valid. Template details:\n")
    write(response, ctx.obj["output_format"])


@click.command(name="generate")
@click.argument("path")
@click.pass_context
@catch_exceptions
def generate_command(ctx, path):
    """
    Prints the template.

    Prints the template used for stack in PATH.
    """
    stack = get_stack(ctx, path)
    write(stack.template.body)
