import logging
import sys
from itertools import cycle
from functools import partial, wraps

import json
import click
import six
import yaml

from boto3.exceptions import Boto3Error
from botocore.exceptions import BotoCoreError, ClientError
from jinja2.exceptions import TemplateError

from sceptre.exceptions import SceptreException
from sceptre.stack_status import StackStatus
from sceptre.stack_status_colourer import StackStatusColourer


def catch_exceptions(func):
    """
    Catches and simplifies expected errors thrown by sceptre.

    catch_exceptions should be used as a decorator.

    :param func: The function which may throw exceptions which should be
        simplified.
    :returns: The decorated function.
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
    command, ignore, command_path, change_set=None
):
    if not ignore:
        msg = "Do you want to {} ".format(command)
        if change_set:
            msg = msg + "change set '{0}' for '{1}'".format(
                change_set, command_path
            )
        else:
            msg = msg + "'{0}'".format(command_path)
        click.confirm(msg, abort=True)


def write(var, output_format="json", no_colour=True):
    """
    Writes ``var`` to stdout. If output_format is set to "json" or "yaml",
    write ``var`` as a JSON or YAML string.

    :param var: The object to print
    :type var: object
    :param output_format: The format to print the output as. Allowed values: \
    "text", "json", "yaml"
    :type output_format: str
    :param no_colour: Whether to colour stack statuses
    :type no_colour: bool
    """
    output = var

    if output_format == "json":
        output = _generate_json(var)
    if output_format == "yaml":
        output = _generate_yaml(var)
    if output_format == "text":
        output = _generate_text(var)
    if not no_colour:
        stack_status_colourer = StackStatusColourer()
        output = stack_status_colourer.colour(str(output))

    click.echo(output)


def _generate_json(stream):
    encoder = CustomJsonEncoder(indent=4)
    if isinstance(stream, list):
        items = []
        for item in stream:
            try:
                if isinstance(item, dict):
                    items.append(item)
                else:
                    items.append(yaml.load(item, Loader=CfnYamlLoader))
            except Exception:
                print("An error occured writing the JSON object.")
        return encoder.encode(items)
    else:
        try:
            return encoder.encode(yaml.load(stream, Loader=CfnYamlLoader))
        except Exception:
            return encoder.encode(stream)


def _generate_yaml(stream):
    if isinstance(stream, list):
        items = []
        for item in stream:
            try:
                if isinstance(item, dict):
                    items.append(
                        yaml.safe_dump(item, default_flow_style=False, explicit_start=True)
                    )
                else:
                    items.append(
                        yaml.safe_dump(
                            yaml.load(item, Loader=CfnYamlLoader),
                            default_flow_style=False, explicit_start=True
                        )
                    )
            except Exception:
                print("An error occured whilst writing the YAML object.")
        return yaml.safe_dump(
            [yaml.load(item, Loader=CfnYamlLoader) for item in items],
            default_flow_style=False, explicit_start=True
        )
    else:
        try:
            return yaml.safe_loads(stream)
        except Exception:
            return stream


def _generate_text(stream):
    if isinstance(stream, list):
        items = []
        for item in stream:
            try:
                if isinstance(item, dict):
                    # use keys as headers, and add a blank row
                    if not items:
                        items = [["Stack"]]
                        items[0].extend(list(next(iter(*item.values()))))
                        items.append(["" for _ in range(len(items[0]))])
                    for k, v in item.items():
                        for r in item[k]:
                            row = [k]
                            row.extend(list(r.values()))
                            items.append(row)
                else:
                    items.append(item)
            except Exception:
                print("An error occured writing the text object.")
        col_widths = [max(len(c) for c in b) for b in zip(*items)]
        rows = []
        for row in items:
            rows.append("".join(
                [field for field, width in zip(row, cycle(col_widths))]
            ))
        return "\n".join(rows)
    return stream


def stack_status_exit_code(statuses):
    if not all(
            status == StackStatus.COMPLETE
            for status in statuses):
        return 1
    else:
        return 0


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
        fmt="[%(asctime)s] - %(message)s",
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


class CustomJsonEncoder(json.JSONEncoder):
    """
    CustomJsonEncoder is a JSONEncoder which encodes all items as JSON by
    calling their __str__() method.
    """

    def default(self, item):
        """
        Returns stringified version of item.

        :param item: An arbitrary object to stringify.
        :type item: object
        :returns: The stringified object.
        :rtype: str
        """
        return str(item)


CFN_FNS = [
    'And',
    'Base64',
    'Cidr',
    'Equals',
    'FindInMap',
    'GetAtt',
    'GetAZs',
    'If',
    'ImportValue',
    'Join',
    'Not',
    'Or',
    'Select',
    'Split',
    'Sub',
    'Transform',
]

CFN_TAGS = [
    'Condition',
    'Ref',
]


def _getatt_constructor(loader, node):
    if isinstance(node.value, six.text_type):
        return node.value.split('.', 1)
    elif isinstance(node.value, list):
        seq = loader.construct_sequence(node)
        for item in seq:
            if not isinstance(item, six.text_type):
                raise ValueError(
                    "Fn::GetAtt does not support complex datastructures")
        return seq
    else:
        raise ValueError("Fn::GetAtt only supports string or list values")


def _tag_constructor(loader, tag_suffix, node):
    if tag_suffix not in CFN_FNS and tag_suffix not in CFN_TAGS:
        raise ValueError("Bad tag: !{tag_suffix}. Supported tags are: "
                         "{supported_tags}".format(
                             tag_suffix=tag_suffix,
                             supported_tags=", ".join(sorted(CFN_TAGS + CFN_FNS))
                         ))

    if tag_suffix in CFN_FNS:
        tag_suffix = "Fn::{tag_suffix}".format(tag_suffix=tag_suffix)

    data = {}
    yield data

    if tag_suffix == 'Fn::GetAtt':
        constructor = partial(_getatt_constructor, (loader, ))
    elif isinstance(node, yaml.ScalarNode):
        constructor = loader.construct_scalar
    elif isinstance(node, yaml.SequenceNode):
        constructor = loader.construct_sequence
    elif isinstance(node, yaml.MappingNode):
        constructor = loader.construct_mapping

    data[tag_suffix] = constructor(node)


class CfnYamlLoader(yaml.SafeLoader):
    pass


CfnYamlLoader.add_multi_constructor("!", _tag_constructor)
