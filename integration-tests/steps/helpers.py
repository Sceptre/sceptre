from sceptre.exceptions import TemplateSceptreHandlerError
from sceptre.exceptions import UnsupportedTemplateFileTypeError


@then('the user is told {message}')
def step_impl(context, message):
    if message == "stack does not exist":
        assert context.error.endswith("does not exist")
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
