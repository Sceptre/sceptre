import click
from click import Context

from sceptre.context import SceptreContext
from sceptre.plan.plan import SceptrePlan

from sceptre.cli.helpers import catch_exceptions, deserialize_json_properties, write

BAD_STATUSES = ["DETECTION_FAILED", "TIMED_OUT"]


@click.group(name="drift")
def drift_group():
    """
    Commands for calling drift detection.
    """
    pass


@drift_group.command(
    name="detect", short_help="Run detect stack drift on running stacks."
)
@click.argument("path")
@click.pass_context
@catch_exceptions
def drift_detect(ctx: Context, path: str):
    """
    Detect stack drift and return stack drift status.

    In the event that the stack does not exist, we return
    a DetectionStatus and StackDriftStatus of STACK_DOES_NOT_EXIST.

    In the event that drift detection times out, we return
    a DetectionStatus and StackDriftStatus of TIMED_OUT.

    The timeout is set at 5 minutes, a value that cannot be configured.
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
    responses = plan.drift_detect()

    output_format = "json" if context.output_format == "json" else "yaml"

    exit_status = 0
    for stack, response in responses.items():
        status = response["DetectionStatus"]
        if status in BAD_STATUSES:
            exit_status += 1
        for key in ["Timestamp", "ResponseMetadata"]:
            response.pop(key, None)
        write(
            {stack.external_name: deserialize_json_properties(response)}, output_format
        )

    exit(exit_status)


@drift_group.command(name="show", short_help="Shows stack drift on running stacks.")
@click.argument("path")
@click.option(
    "-D", "--drifted", is_flag=True, default=False, help="Filter out in sync resources."
)
@click.pass_context
@catch_exceptions
def drift_show(ctx, path, drifted):
    """
    Show stack drift on deployed stacks.

    In the event that the stack does not exist, we return
    a StackResourceDriftStatus of STACK_DOES_NOT_EXIST.

    In the event that drift detection times out, we return
    a StackResourceDriftStatus of TIMED_OUT.

    The timeout is set at 5 minutes, a value that cannot be configured.
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
    responses = plan.drift_show(drifted)

    output_format = "json" if context.output_format == "json" else "yaml"

    exit_status = 0
    for stack, (status, response) in responses.items():
        if status in BAD_STATUSES:
            exit_status += 1
        write(
            {stack.external_name: deserialize_json_properties(response)}, output_format
        )

    exit(exit_status)
