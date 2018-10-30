import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import (
          catch_exceptions,
          get_stack_or_stack_group,
          write
        )
from sceptre.plan.plan import SceptrePlan


@click.group(name="list")
def list_group():
    """
    Commands for listing attributes of stacks.

    """
    pass


@list_group.command(name="resources")
@click.argument("path")
@click.pass_context
@catch_exceptions
def list_resources(ctx, path):
    """
    List resources for stack or stack_group.

    """
    context = SceptreContext(
                path=path,
                project_path=ctx.obj.get("project_path", None),
                user_variables=ctx.obj.get("user_variables", {}),
                options=ctx.obj.get("options", {}),
                output_format=ctx.obj["output_format"]
            )

    stack, stack_group = get_stack_or_stack_group(context, path)
    action = 'describe_resources'

    if stack:
        plan = SceptrePlan(context, action, stack)
        write(plan.execute(), context.output_format)
    elif stack_group:
        plan = SceptrePlan(context, action, stack_group)
        write(plan.execute(), context.output_format)


@list_group.command(name="outputs")
@click.argument("path")
@click.option(
    "-e", "--export", type=click.Choice(["envvar"]),
    help="Specify the export formatting."
)
@click.pass_context
@catch_exceptions
def list_outputs(ctx, path, export):
    """
    List outputs for stack.

    """
    context = SceptreContext(
                path=path,
                project_path=ctx.obj.get("project_path", None),
                user_variables=ctx.obj.get("user_variables", {}),
                options=ctx.obj.get("options", {})
            )

    stack, _ = get_stack_or_stack_group(context, path)
    action = 'describe_outputs'
    plan = SceptrePlan(context, action, stack)
    response = plan.execute()

    if export == "envvar":
        write("\n".join(
            [
                "export SCEPTRE_{0}={1}".format(
                    output["OutputKey"], output["OutputValue"]
                )
                for output in response
            ]
        ))
    else:
        write(response, context.output_format)


@list_group.command(name="change-sets")
@click.argument("path")
@click.pass_context
@catch_exceptions
def list_change_sets(ctx, path):
    """
    List change sets for stack.

    """
    context = SceptreContext(
                path=path,
                project_path=ctx.obj.get("project_path", None),
                user_variables=ctx.obj.get("user_variables", {}),
                options=ctx.obj.get("options", {})
            )

    stack, _ = get_stack_or_stack_group(context, path)
    action = 'list_change_sets'
    plan = SceptrePlan(context, action, stack)
    response = plan.execute()

    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        del response['ResponseMetadata']
    write(response, context.output_format)
