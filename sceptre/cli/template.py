import click
import webbrowser

from sceptre.cli.helpers import catch_exceptions, get_stack_or_env, write


@click.command(name="validate")
@click.argument("path")
@click.pass_context
@catch_exceptions
def validate_command(ctx, path):
    """
    Validates the template.

    Validates the template used for stack in PATH.
    """
    stack, _ = get_stack_or_env(ctx, path)
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
    stack, _ = get_stack_or_env(ctx, path)
    write(stack.template.body)


@click.command(name="estimate-cost")
@click.argument("path")
@click.pass_context
@catch_exceptions
def estimate_cost_command(ctx, path):
    """
    Estimates the cost of the template.
    Prints a URI to STOUT that provides an estimated cost based on the
    resources in the stack. This command will also attempt to open a web
    browser with the returned URI.
    """
    stack, _ = get_stack_or_env(ctx, path)
    response = stack.template.estimate_cost()

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        del response['ResponseMetadata']
        click.echo("View the estimated cost at:")
        response = response["Url"]
        webbrowser.open(response, new=2)
    write(response + "\n", 'str')
