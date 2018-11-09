import click
import webbrowser

from sceptre.context import SceptreContext
from sceptre.cli.helpers import (
          catch_exceptions,
          get_stack_or_stack_group,
          write
        )
from sceptre.plan.plan import SceptrePlan


@click.command(name="validate")
@click.argument("path")
@click.pass_context
@catch_exceptions
def validate_command(ctx, path):
    """
    Validates the template.

    Validates the template used for stack in PATH.
    """
    context = SceptreContext(
                command_path=path,
                project_path=ctx.obj.get("project_path"),
                user_variables=ctx.obj.get("user_variables"),
                options=ctx.obj.get("options"),
                output_format=ctx.obj.get("output_format")
            )

    stack, _ = get_stack_or_stack_group(context)
    action = 'validate'
    plan = SceptrePlan(context, action, stack.template)
    response = plan.execute()

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        del response['ResponseMetadata']
        click.echo("Template is valid. Template details:\n")
    write(response, context.output_format)


@click.command(name="generate")
@click.argument("path")
@click.pass_context
@catch_exceptions
def generate_command(ctx, path):
    """
    Prints the template.

    Prints the template used for stack in PATH.
    """
    context = SceptreContext(
                command_path=path,
                project_path=ctx.obj.get("project_path"),
                user_variables=ctx.obj.get("user_variables"),
                options=ctx.obj.get("options")
            )

    stack, _ = get_stack_or_stack_group(context)
    action = 'generate'
    plan = SceptrePlan(context, action, stack.template)
    write(plan.execute())


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
    action = 'estimate_cost'
    context = SceptreContext(
                command_path=path,
                project_path=ctx.obj.get("project_path"),
                user_variables=ctx.obj.get("user_variables"),
                options=ctx.obj.get("options"),
                output_format=ctx.obj.get("output_format")
            )

    stack, _ = get_stack_or_stack_group(context)
    plan = SceptrePlan(context, action, stack.template)
    response = plan.execute()

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        del response['ResponseMetadata']
        click.echo("View the estimated cost at:")
        response = response["Url"]
        webbrowser.open(response, new=2)
    write(response + "\n", 'str')
