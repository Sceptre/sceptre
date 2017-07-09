from behave import *
import os

from sceptre.exceptions import TemplateSceptreHandlerError
from sceptre.exceptions import UnsupportedTemplateFileTypeError


@then('the user is told {message}')
def step_impl(context, message):
    if message == "stack does not exist":
        assert context.error.endswith("does not exist")
    elif message == "the change set does not exist":
        error_message = context.error.response['Error']['Message']
        assert error_message.endswith("does not exist")
    elif message == "the template is valid":
        assert context.response["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert context.error is None
    elif message == "the template is malformed":
        assert context.error.endswith("[Malformed]")
    elif message == "template does not have sceptre_handler":
        message = "The template does not have the required "
        "'sceptre_handler(sceptre_user_data)' function."
        assert context.error.message == message
    elif message == "attribute error":
        assert isinstance(context.error, TemplateSceptreHandlerError)
    elif message == "template format is unsupported":
        assert isinstance(context.error, UnsupportedTemplateFileTypeError)
    elif message == "change set failed to create":
        assert False


def read_template_file(context, template_name):
    path = os.path.join(context.sceptre_dir, "templates", template_name)
    with open(path) as template:
        return template.read()


def get_cloudformation_stack_name(context, stack_name):
    return "-".join(
        [context.project_code, stack_name.replace("/", "-")]
    )
