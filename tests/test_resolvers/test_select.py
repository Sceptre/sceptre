from unittest.mock import Mock

from sceptre.resolvers import Resolver
from sceptre.resolvers.select import Select


class MyListResolver(Resolver):
    def resolve(self):
        return ["first", "second", "third"]


class ItemResolver(Resolver):
    def resolve(self):
        return self.argument


class TestSelect:
    def test_resolve__second_arg_is_list_resolver__selects_item_at_list_index(self):
        argument = [1, MyListResolver()]
        select = Select(argument, Mock())
        resolved = select.resolve()
        expected = "second"
        assert expected == resolved

    def test_resolve__second_arg_is_list_of_resolvers__selects_item_at_list_index(self):
        argument = [
            1,
            [ItemResolver("first"), ItemResolver("second"), ItemResolver("third")],
        ]
        select = Select(argument, Mock())
        resolved = select.resolve()
        expected = "second"
        assert expected == resolved
