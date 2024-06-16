import logging
from unittest import TestCase

import pytest

from sceptre.exceptions import TemplateHandlerArgumentsInvalidError
from sceptre.template_handlers import TemplateHandler


class MockTemplateHandler(TemplateHandler):
    def __init__(self, *args, **kwargs):
        super(MockTemplateHandler, self).__init__(*args, **kwargs)

    def schema(self):
        return {
            "type": "object",
            "properties": {"argument": {"type": "string"}},
            "required": ["argument"],
        }

    def handle(self):
        return "TestTemplateHandler"


class TestTemplateHandlers(TestCase):
    def test_template_handler_validates_schema(self):
        handler = MockTemplateHandler(name="mock", arguments={"argument": "test"})
        handler.validate()

    def test_template_handler_errors_when_arguments_invalid(self):
        with pytest.raises(TemplateHandlerArgumentsInvalidError):
            handler = MockTemplateHandler(
                name="mock", arguments={"non-existent": "test"}
            )
            handler.validate()

    def test_logger__logs_have_stack_name_prefix(self):
        template_handler = MockTemplateHandler(
            name="mock", arguments={"argument": "test"}
        )
        with self.assertLogs(template_handler.logger.name, logging.INFO) as handler:
            template_handler.logger.info("Bonjour")

        assert handler.records[0].message == f"{template_handler.name} - Bonjour"
