import contextlib
import os
import sys
from functools import wraps
from json import JSONEncoder

import click
import logging
import yaml

from boto3.exceptions import Boto3Error
from botocore.exceptions import BotoCoreError, ClientError
from jinja2.exceptions import TemplateError

from sceptre.exceptions import SceptreException, RecursiveFlagMissingError
from sceptre.exceptions import StackPathRequiredError, StackConfigNotFoundError
from sceptre.stack_status_colourer import StackStatusColourer
from sceptre.environment import Environment


def catch_exceptions(func):
    """
    Catches and simplifies expected errors thrown by sceptre.

    catch_exceptions should be used as a decorator.

    :param func: The function which may throw exceptions which should be
        simplified.
    :type func: func
    :returns: The decorated function.
    :rtype: func
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        """
        Invokes ``func``, catches expected errors, prints the error message and
        exits sceptre with a non-zero exit code.
        """
        try:
            return func(*args, **kwargs)
        except (SceptreException, BotoCoreError, ClientError, Boto3Error,
                TemplateError) as error:
            write(error)
            sys.exit(1)

    return decorated


def write(var, output_format="str", no_colour=True):
    """
    Writes ``var`` to stdout. If output_format is set to "json" or "yaml",
    write ``var`` as a JSON or YAML string.

    :param var: The object to print
    :type var: obj
    :param output_format: The format to print the output as. Allowed values: \
    "str", "json", "yaml"
    :type output_format: str
    :param no_colour: Whether to color stack statuses
    :type no_colour: bool
    """
    if output_format == "json":
        encoder = CustomJsonEncoder()
        stream = encoder.encode(var)
    if output_format == "yaml":
        stream = yaml.safe_dump(var, default_flow_style=False)
    if output_format == "str":
        stream = var

    if not no_colour:
        stack_status_colourer = StackStatusColourer()
        stream = stack_status_colourer.colour(stream)

    click.echo(stream)


@contextlib.contextmanager
def change_set(stack, name):
    """
    Creates and yields and deletes a change set.

    :param stack: The stack to create the change set for.
    :type stack: sceptre.stack.Stack
    :param name: The name of the change set.
    :type name: str
    """
    stack.create_change_set(name)
    try:
        yield
    finally:
        stack.delete_change_set(name)


def get_stack_and_env(ctx, path, recursive):
    """
    Parses the path to generate relevant Envrionment and Stack object.

    :param ctx: Cli context.
    :type ctx: click.Context
    :param path: Path to either stack config or environment folder.
    :type path: str
    :param recursive: Flag to allow environment level actions.
    :type recursive: bool
    """
    stack_name = None

    path, ext = os.path.splitext(path)
    if ext:
        path, stack_name = os.path.split(path)

    env = Environment(ctx.obj["sceptre_dir"], path, ctx.obj["options"])

    if stack_name:
        try:
            stack = env.stacks[stack_name]
        except KeyError:
            raise StackConfigNotFoundError()
        return (stack, env)

    elif not stack_name and not recursive:
        raise RecursiveFlagMissingError("Use recursive flag.")

    return (None, env)


def get_stack(ctx, path):
    """
    Retrieves the Stack object for path to stack config.

    :param stack: The stack to create the change set for.
    :type stack: sceptre.stack.Stack
    :param name: The name of the change set.
    :type name: str
    """
    stack, _ = get_stack_and_env(ctx, path, False)
    if not stack:
        raise StackPathRequiredError("Path to a stack required.")
    return stack


def setup_logging(debug, no_colour):
    """
    Sets up logging.

    By default, the python logging module is configured to push logs to stdout
    as long as their level is at least INFO. The log format is set to
    "[%(asctime)s] - %(name)s - %(message)s" and the date format is set to
    "%Y-%m-%d %H:%M:%S".

    After this function has run, modules should:

    .. code:: python

        import logging

        logging.getLogger(__name__).info("my log message")

    :param debug: A flag indication whether to turn on debug logging.
    :type debug: bool
    :no_colour: A flag to indicating whether to turn off coloured output.
    :type no_colour: bool
    :returns: A logger.
    :rtype: logging.Logger
    """
    if debug:
        sceptre_logging_level = logging.DEBUG
        logging.getLogger("botocore").setLevel(logging.INFO)
    else:
        sceptre_logging_level = logging.INFO
        # Silence botocore logs
        logging.getLogger("botocore").setLevel(logging.CRITICAL)

    formatter_class = logging.Formatter if no_colour else ColouredFormatter

    formatter = formatter_class(
        fmt="[%(asctime)s] - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    log_handler = logging.StreamHandler()
    log_handler.setFormatter(formatter)
    logger = logging.getLogger("sceptre")
    logger.addHandler(log_handler)
    logger.setLevel(sceptre_logging_level)
    return logger


def simplify_change_set_description(response):
    """
    Simplies the response from the AWS describe change set API.

    :param response: The original api response.
    :type response: dict
    :returns: A more concise description of the change set.
    :rtype: dict
    """
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


class ColouredFormatter(logging.Formatter):
    """
    ColouredFormatter add colours to all stack statuses that appear in log
    messages.
    """

    stack_status_colourer = StackStatusColourer()

    def format(self, record):
        """
        Colours and returns all stack statuses in ``record``.

        :param record: The log item to format.
        :type record: str
        :returns: str
        """
        response = super(ColouredFormatter, self).format(record)
        coloured_response = self.stack_status_colourer.colour(response)
        return coloured_response


class CustomJsonEncoder(JSONEncoder):
    """
    CustomJsonEncoder is a JSONEncoder which encodes all items as JSON by
    calling their __str__() method.
    """

    def default(self, item):
        """
        Returns stringified version of item.

        :param item: An arbitrary object to stringify.
        :type item: obj
        :returns: The stringified object.
        :rtype: str
        """
        return str(item)
