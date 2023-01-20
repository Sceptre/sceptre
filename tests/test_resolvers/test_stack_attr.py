from unittest.mock import Mock

import pytest

from sceptre.resolvers.stack_attr import StackAttr
from sceptre.stack import Stack


class TestResolver(object):
    def setup_method(self, test_method):
        self.stack_group_config = {}
        self.stack = Mock(spec=Stack, stack_group_config=self.stack_group_config)

        self.resolver = StackAttr(stack=self.stack)

    def test__resolve__returns_attribute_off_stack(self):
        self.resolver.argument = "testing_this"
        self.stack.testing_this = "hurray!"
        result = self.resolver.resolve()

        assert result == "hurray!"

    def test_resolve__nested_attribute__accesses_nested_value(self):
        self.stack.testing_this = {"top": [{"thing": "first"}, {"thing": "second"}]}

        self.resolver.argument = "testing_this.top.1.thing"
        result = self.resolver.resolve()

        assert result == "second"

    def test_resolve__attribute_not_defined__accesses_it_off_stack_group_config(self):
        self.stack.stack_group_config["testing_this"] = {
            "top": [{"thing": "first"}, {"thing": "second"}]
        }

        self.resolver.argument = "testing_this.top.1.thing"
        result = self.resolver.resolve()

        assert result == "second"

    @pytest.mark.parametrize(
        "config,attr_name",
        [
            ("template", "template_handler_config"),
            ("protect", "protected"),
            ("stack_name", "external_name"),
            ("stack_tags", "tags"),
        ],
    )
    def test_resolve__accessing_attribute_renamed_on_stack__resolves_correct_value(
        self, config, attr_name
    ):
        setattr(self.stack, attr_name, "value")
        self.resolver.argument = config

        result = self.resolver.resolve()

        assert result == "value"

    def test_resolve__attribute_not_defined__raises_attribute_error(self):
        self.resolver.argument = "nonexistant"

        with pytest.raises(AttributeError):
            self.resolver.resolve()
