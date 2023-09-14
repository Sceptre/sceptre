import logging
import click

from sceptre.context import SceptreContext
from sceptre.cli.helpers import catch_exceptions, write
from sceptre.plan.plan import SceptrePlan

from typing import List, Dict

logger = logging.getLogger(__name__)


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
    \f

    :param path: Path to execute the command on.
    :type path: str
    """
    context = SceptreContext(
        command_path=path,
        command_params=ctx.params,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        options=ctx.obj.get("options"),
        output_format=ctx.obj.get("output_format"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
    )
    plan = SceptrePlan(context)

    responses = [
        response for response in plan.describe_resources().values() if response
    ]

    write(responses, context.output_format)


# flake8: noqa: C901
def write_outputs(export, responses, plan, context):
    """
    Helper function for list outputs.
    """
    # Legacy. This option was added in the initial commit of the project,
    # although its intended use case is unclear. It may relate to a feature
    # that had been removed prior to the initial commit.
    if export == "envvar":
        for response in responses:
            for stack in response.values():
                for output in stack:
                    write(
                        "export SCEPTRE_{0}='{1}'".format(
                            output.get("OutputKey"), output.get("OutputValue")
                        ),
                        "text",
                    )

    # Format outputs as !stack_output references.
    elif export == "stackoutput":
        for response in responses:
            for stack_name, stack in response.items():
                for output in stack:
                    write(
                        "!stack_output {0}.yaml::{1} [{2}]".format(
                            stack_name,
                            output.get("OutputKey"),
                            output.get("OutputValue"),
                        ),
                        "text",
                    )

    # Format outputs as !stack_output_external references.
    elif export == "stackoutputexternal":
        stack_names = {stack.name: stack.external_name for stack in plan.graph}
        for response in responses:
            for stack_name, stack in response.items():
                for output in stack:
                    write(
                        "!stack_output_external {0}::{1} [{2}]".format(
                            stack_names[stack_name],
                            output.get("OutputKey"),
                            output.get("OutputValue"),
                        ),
                        "text",
                    )

    # Legacy. The output here is somewhat confusing in that
    # outputs are organised in keys that only have meaning inside
    # Sceptre.
    else:
        write(responses, context.output_format)


@list_group.command(name="outputs")
@click.argument("path")
@click.option(
    "-e",
    "--export",
    type=click.Choice(["envvar", "stackoutput", "stackoutputexternal"]),
    help="Specify the export formatting.",
)
@click.pass_context
@catch_exceptions
def list_outputs(ctx, path, export):
    """
    List outputs for stack.
    \f
    :param path: Path to execute the command on.
    :type path: str
    :param export: Specify the export formatting.
    :type export: str
    """
    context = SceptreContext(
        command_path=path,
        command_params=ctx.params,
        project_path=ctx.obj.get("project_path", None),
        user_variables=ctx.obj.get("user_variables", {}),
        options=ctx.obj.get("options", {}),
        output_format=ctx.obj.get("output_format"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
    )

    plan = SceptrePlan(context)
    responses = [response for response in plan.describe_outputs().values() if response]

    write_outputs(export, responses, plan, context)


@list_group.command(name="change-sets")
@click.option("-U", "--url", is_flag=True, help="Instead write a URL.")
@click.argument("path")
@click.pass_context
@catch_exceptions
def list_change_sets(ctx, path, url):
    """
    List change sets for stack.
    \f

    :param path: Path to execute the command on.
    :type path: str
    :param url: Write out a console URL instead.
    :type url: bool
    """
    context = SceptreContext(
        command_path=path,
        command_params=ctx.params,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        output_format=ctx.obj.get("output_format"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
    )

    plan = SceptrePlan(context)

    responses = [
        response for response in plan.list_change_sets(url).values() if response
    ]

    for response in responses:
        write(response, context.output_format)


@list_group.command(name="stacks")
@click.argument("path")
@click.pass_context
@catch_exceptions
def list_stacks(ctx, path):
    """
    List sceptre stack config attributes,
    \f

    :param path: Path to execute the command on or path to stack group
    """
    context = SceptreContext(
        command_path=path,
        command_params=ctx.params,
        project_path=ctx.obj.get("project_path"),
        user_variables=ctx.obj.get("user_variables"),
        output_format=ctx.obj.get("output_format"),
        options=ctx.obj.get("options"),
        ignore_dependencies=ctx.obj.get("ignore_dependencies"),
    )

    plan = SceptrePlan(context)

    output = {f"{stack.name}.yaml": stack.external_name for stack in plan.graph}
    output_format = "json" if context.output_format == "json" else "yaml"
    write(output, output_format)
