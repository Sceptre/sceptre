from behave import *
import os
import time

import jinja2.exceptions

from botocore.exceptions import ClientError
from sceptre.exceptions import TemplateSceptreHandlerError
from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.exceptions import StackDoesNotExistError


@then('the user is told "{message}"')
def step_impl(context, message):
    if message == "stack does not exist":
        msg = context.error.response['Error']['Message']
        assert msg.endswith("does not exist")
    elif message == "change set does not exist":
        msg = context.error.response['Error']['Message']
        assert msg.endswith("does not exist")
    elif message == "the template is valid":
        for stack, status in context.response.items():
            assert status["ResponseMetadata"]["HTTPStatusCode"] == 200
    elif message == "the template is malformed":
        msg = context.error.response['Error']['Message']
        assert msg.startswith("Template format error")
    else:
        raise Exception("Step has incorrect message")


@then('no exception is raised')
def step_impl(context):
    assert (context.error is None)


@then('a "{exception_type}" is raised')
def step_impl(context, exception_type):
    if exception_type == "TemplateSceptreHandlerError":
        assert isinstance(context.error, TemplateSceptreHandlerError)
    elif exception_type == "UnsupportedTemplateFileTypeError":
        assert isinstance(context.error, UnsupportedTemplateFileTypeError)
    elif exception_type == "StackDoesNotExistError":
        assert isinstance(context.error, StackDoesNotExistError)
    elif exception_type == "ClientError":
        assert isinstance(context.error, ClientError)
    elif exception_type == "AttributeError":
        assert isinstance(context.error, AttributeError)
    elif exception_type == "UndefinedError":
        assert isinstance(context.error, jinja2.exceptions.UndefinedError)
    else:
        raise Exception("Step has incorrect message")


@given('stack_group "{stack_group}" has AWS config "{config}" set')
def step_impl(context, stack_group, config):
    config_path = os.path.join(
        context.sceptre_dir, "config", stack_group, config
    )

    os.environ['AWS_CONFIG_FILE'] = config_path


def read_template_file(context, template_name):
    path = os.path.join(context.sceptre_dir, "templates", template_name)
    with open(path) as template:
        return template.read()


def get_cloudformation_stack_name(context, stack_name):
    return "-".join(
        [context.project_code, stack_name.replace("/", "-")]
    )


def retry_boto_call(func, *args, **kwargs):
    delay = 2
    max_retries = 150
    attempts = 0
    while attempts < max_retries:
        attempts += 1
        try:
            response = func(*args, **kwargs)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'Throttling':
                time.sleep(delay)
            else:
                raise e
