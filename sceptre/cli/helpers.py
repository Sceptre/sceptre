import logging
import os
import sys
from functools import wraps
from json import JSONEncoder

import click
import yaml

from sceptre.config_reader import ConfigReader

from boto3.exceptions import Boto3Error
from botocore.exceptions import BotoCoreError, ClientError
from jinja2.exceptions import TemplateError

from sceptre.exceptions import SceptreException
from sceptre.stack_status_colourer import StackStatusColourer


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


def confirmation(
    command, ignore, stack_group=None, stack=None, change_set=None
):
    if not ignore:
        msg = "Do you want to {} ".format(command)
        if stack_group:
            msg = msg + "stack_group '{0}'?".format(stack_group)
        elif change_set and stack:
            msg = msg + "change set '{0}' for stack '{1}'".format(
                change_set, stack
            )
        elif stack:
            msg = msg + "stack '{0}'".format(stack)
        click.confirm(msg, abort=True)


def write(var, output_format="str", no_colour=True):
    """
    Writes ``var`` to stdout. If output_format is set to "json" or "yaml",
    write ``var`` as a JSON or YAML string.

    :param var: The object to print
    :type var: obj
    :param output_format: The format to print the output as. Allowed values: \
    "str", "json", "yaml"
    :type output_format: str
    :param no_colour: Whether to colour stack statuses
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


def get_stack_or_stack_group(ctx, path):
    """
    Parses the path to generate relevant Stack Group and Stack object.

    :param ctx: Cli context.
    :type ctx: click.Context
    :param path: Path to either stack config or stack_group folder.
    :type path: str
    """
    stack = None
    stack_group = None

    config_reader = ConfigReader(
        ctx.obj["sceptre_dir"], ctx.obj["user_variables"]
    )

    if os.path.splitext(path)[1]:
        stack = config_reader.construct_stack(path)
    else:
        stack_group = config_reader.construct_stack_group(path)

    return (stack, stack_group)


def get_stack(ctx, path):
    """
    Parses the path to generate relevant StackGroup and Stack object.

    :param ctx: Cli context.
    :type ctx: click.Context
    :param path: Path to either stack config or stack_group folder.
    :type path: str
    """
    return ConfigReader(
        ctx.obj["sceptre_dir"], ctx.obj["options"]
    ).construct_stack(path)


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
