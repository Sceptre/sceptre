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

    def test_get_jinja_vars_includes_stack_config(self):
        stack_config = {
            "stack_name": "my-custom-stack",
            "parameters": {"Param1": "Value1"},
        }
        handler = MockTemplateHandler(
            name="dev/vpc",
            arguments={"argument": "test"},
            stack_config=stack_config,
        )
        jinja_vars = handler._get_jinja_vars()
        assert jinja_vars["stack_config"] == stack_config

    def test_stack_config_flows_from_stack_to_jinja_vars(self):
        """Test that stack config reaches the Jinja2 template context."""
        from unittest.mock import patch, MagicMock
        from sceptre.stack import Stack

        stack = Stack(
            name="dev/vpc",
            project_code="my_project",
            region="us-east-1",
            template_handler_config={"type": "file", "path": "vpc.json"},
            external_name="my-custom-stack-name",
            config={
                "stack_name": "my-custom-stack-name",
                "project_code": "my_project",
                "region": "us-east-1",
            },
        )

        with patch(
            "sceptre.template.Template._get_handler_of_type"
        ) as mock_get_handler:
            mock_handler_class = MagicMock()
            mock_get_handler.return_value = mock_handler_class
            mock_handler_instance = MagicMock()
            mock_handler_class.return_value = mock_handler_instance
            mock_handler_instance.handle.return_value = "{}"

            _ = stack.template.body

            call_kwargs = mock_handler_class.call_args[1]
            assert call_kwargs["stack_config"]["stack_name"] == "my-custom-stack-name"
