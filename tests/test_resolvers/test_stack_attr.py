from unittest.mock import Mock

from sceptre.resolvers.stack_attr import StackAttr


class TestResolver(object):

    def setup_method(self, test_method):
        self.stack = Mock()

        self.resolver = StackAttr(stack=self.stack)

    def test__resolve__returns_attribute_off_stack(self):
        self.resolver.argument = 'testing_this'
        self.stack.testing_this = 'hurray!'
        result = self.resolver.resolve()

        assert result == 'hurray!'

    def test_resolve__nested_attribute__accesses_nested_value(self):
        self.stack.testing_this = {
            'top': [
                {'thing': 'first'},
                {'thing': 'second'}
            ]
        }

        self.resolver.argument = 'testing_this.top.1.thing'
        result = self.resolver.resolve()

        assert result == 'second'
