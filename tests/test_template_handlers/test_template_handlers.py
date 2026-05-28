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

    def test_get_jinja_vars_includes_sceptre_user_data(self):
        user_data = {"vpc_cidr": "10.0.0.0/16"}
        handler = MockTemplateHandler(
            name="mock",
            arguments={"argument": "test"},
            sceptre_user_data=user_data,
        )
        jinja_vars = handler._get_jinja_vars()
        assert jinja_vars["sceptre_user_data"] == user_data

    def test_get_jinja_vars_includes_stack_group_config(self):
        stack_group_config = {
            "project_code": "my_project",
            "region": "us-east-1",
            "environment": "production",
        }
        handler = MockTemplateHandler(
            name="mock",
            arguments={"argument": "test"},
            stack_group_config=stack_group_config,
        )
        jinja_vars = handler._get_jinja_vars()
        assert jinja_vars["stack_group_config"] == stack_group_config

    def test_get_jinja_vars_with_no_user_data_or_config(self):
        handler = MockTemplateHandler(
            name="mock",
            arguments={"argument": "test"},
        )
        jinja_vars = handler._get_jinja_vars()
        assert jinja_vars["sceptre_user_data"] is None
        assert jinja_vars["stack_group_config"] == {}
