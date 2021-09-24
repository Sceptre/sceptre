import pytest

from sceptre.exceptions import TemplateHandlerArgumentsInvalidError
from sceptre.template_handlers import TemplateHandler


class MockTemplateHandler(TemplateHandler):
    def __init__(self, *args, **kwargs):
        super(MockTemplateHandler, self).__init__(*args, **kwargs)

    def schema(self):
        return {
            "type": "object",
            "properties": {
                "argument": {"type": "string"}
            },
            "required": ["argument"]
        }

    def handle(self):
        return "TestTemplateHandler"


class TestTemplateHandlers(object):
    def test_template_handler_validates_schema(self):
        handler = MockTemplateHandler(name="mock", arguments={"argument": "test"})
        handler.validate()

    def test_template_handler_errors_when_arguments_invalid(self):
        with pytest.raises(TemplateHandlerArgumentsInvalidError):
            handler = MockTemplateHandler(name="mock", arguments={"non-existent": "test"})
            handler.validate()
