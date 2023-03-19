from unittest.mock import Mock

import pytest

from sceptre.exceptions import InvalidResolverArgumentError
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

    def test_resolve__negative_index__selects_in_reverse(self):
        argument = [-1, MyListResolver()]
        select = Select(argument, Mock())
        resolved = select.resolve()
        expected = "third"
        assert expected == resolved

    def test_resolve__can_select_key_from_dict(self):
        argument = ["something", ItemResolver({"something": 123})]
        select = Select(argument, Mock())
        resolved = select.resolve()
        expected = 123
        assert expected == resolved

    @pytest.mark.parametrize(
        "bad_argument",
        [
            pytest.param("just a string", id="just a string"),
            pytest.param([123, "something"], id="second item is not list or dict"),
            pytest.param([99, [1, 2]], id="index out of bounds"),
            pytest.param(["hello", [1, 2]], id="string index on list"),
            pytest.param(["hello", {"something": "else"}], id="key not present"),
            pytest.param(["first", ["second"], "third"], id="too many items"),
        ],
    )
    def test_resolve__invalid_arguments__raises_invalid_resolver_argument_error(
        self, bad_argument
    ):
        select = Select(bad_argument, Mock())
        with pytest.raises(InvalidResolverArgumentError):
            select.resolve()
