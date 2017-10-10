import click

from helpers import catch_exceptions, get_stack, get_stack_and_env, write


@click.group(name="list")
def list_group():
    """
    Commands for listing attributes of stacks.

    """
    pass


@list_group.command(name="resources")
@click.argument("path")
@click.option("-r", "--recursive", is_flag=True)
@click.pass_context
@catch_exceptions
def list_resources(ctx, path, recursive):
    """
    List resources for stack or environment.

    """
    output_format = ctx.obj["output_format"]
    stack, env = get_stack_and_env(ctx, path, recursive)

    if stack:
        write(stack.describe_resources(), output_format)
    else:
        write(env.describe_resources(), output_format)


@list_group.command(name="outputs")
@click.argument("path")
@click.option("-e", "--export", type=click.Choice(["envvar"]))
@click.pass_context
@catch_exceptions
def list_outputs(ctx, path, export):
    """
    List outputs for stack.

    """
    stack = get_stack(ctx, path)
    response = stack.describe_outputs()

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
        write(response, ctx.obj["output_format"])


@list_group.command(name="change-sets")
@click.argument("path")
@click.pass_context
@catch_exceptions
def list_change_sets(ctx, path):
    """
    List change sets for stack.

    """
    stack = get_stack(ctx, path)
    response = stack.list_change_sets()
    formatted_response = {
        k: v
        for k, v in response.items()
        if k != "ResponseMetadata"
    }
    write(formatted_response, ctx.obj["output_format"])


@click.group(name="describe")
def describe_group():
    """
    Commands for describing attributes of stacks.
    """
    pass


@describe_group.command(name="change-set")
@click.argument("path")
@click.argument("change-set-name")
@click.option("-v", "--verbose", is_flag=True)
@click.pass_context
@catch_exceptions
def describe_change_set(ctx, path, change_set_name, verbose):
    """
    Describes the change set.

    """
    stack = get_stack(ctx, path)
    description = stack.describe_change_set(change_set_name)
    if not verbose:
        description = _simplify_change_set_description(description)
    write(description, ctx.obj["output_format"])


@describe_group.command(name="policy")
@click.argument("path")
@click.pass_context
@catch_exceptions
def describe_policy(ctx, path):
    """
    Displays the stack policy used.

    """
    stack = get_stack(ctx, path)
    response = stack.get_policy()
    write(response.get('StackPolicyBody', {}))


def _simplify_change_set_description(response):
    desired_response_items = [
        "ChangeSetName",
        "CreationTime",
        "ExecutionStatus",
        "StackName",
        "Status",
        "StatusReason"
    ]
    desired_resource_changes = [
        "Action",
        "LogicalResourceId",
        "PhysicalResourceId",
        "Replacement",
        "ResourceType",
        "Scope"
    ]
    formatted_response = {
        k: v
        for k, v in response.items()
        if k in desired_response_items
    }
    formatted_response["Changes"] = [
        {
            "ResourceChange": {
                k: v
                for k, v in change["ResourceChange"].items()
                if k in desired_resource_changes
            }
        }
        for change in response["Changes"]
    ]
    return formatted_response
