import logging
import webbrowser
import click

from deprecation import deprecated

from sceptre import __version__
from sceptre.cli.helpers import catch_exceptions, write
from sceptre.context import SceptreContext
from sceptre.helpers import null_context
from sceptre.plan.plan import SceptrePlan
from sceptre.resolvers.placeholders import use_resolver_placeholders_on_error

logger = logging.getLogger(__name__)


@click.command(name="validate", short_help="Validates the template.")
@click.option(
    "-n",
    "--no-placeholders",
    is_flag=True,
    help="If True, no placeholder values will be supplied for resolvers that cannot be resolved.",
)
@click.argument("path")
@click.pass_context
@catch_exceptions
def validate_command(ctx, no_placeholders, path):
    """
    Validates the template used for stack in PATH.
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

    execution_context = (
        null_context() if no_placeholders else use_resolver_placeholders_on_error()
    )
    with execution_context:
        responses = plan.validate()

    for stack, response in responses.items():
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            del response["ResponseMetadata"]
            click.echo("Template {} is valid. Template details:\n".format(stack.name))
        write(response, context.output_format)


@click.command(name="generate", short_help="Prints the template.")
@click.option(
    "-n",
    "--no-placeholders",
    is_flag=True,
    help="If True, no placeholder values will be supplied for resolvers that cannot be resolved.",
)
@click.argument("path")
@click.pass_context
@catch_exceptions
@deprecated("4.2.0", "5.0.0", __version__, "Use dump template instead.")
def generate_command(ctx, no_placeholders, path):
    """
    Prints the template used for stack in PATH.
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

    execution_context = (
        null_context() if no_placeholders else use_resolver_placeholders_on_error()
    )
    with execution_context:
        responses = plan.generate()

    output = [template for template in responses.values()]
    write(output, context.output_format)


@click.command(name="estimate-cost", short_help="Estimates the cost of the template.")
@click.argument("path")
@click.pass_context
@catch_exceptions
def estimate_cost_command(ctx, path):
    """
    Prints a URI to STOUT that provides an estimated cost based on the
    resources in the stack. This command will also attempt to open a web
    browser with the returned URI.
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
    responses = plan.estimate_cost()

    for stack, response in responses.items():
        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            del response["ResponseMetadata"]
            click.echo("View the estimated cost for {} at:".format(stack.name))
            response = response["Url"]
            webbrowser.open(response, new=2)
        write(response + "\n", "text")


@click.command(name="fetch-remote-template", short_help="Prints the remote template.")
@click.argument("path")
@click.pass_context
@catch_exceptions
def fetch_remote_template_command(ctx, path):
    """
    Prints the remote template used for stack in PATH.
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
    responses = plan.fetch_remote_template()
    output = []
    for stack, template in responses.items():
        if template is None:
            logger.warning(f"{stack.external_name} does not exist")
        else:
            output.append(template)

    write(output, context.output_format)
