from unittest.mock import Mock

import pytest

from sceptre.exceptions import InvalidResolverArgumentError
from sceptre.resolvers import Resolver
from sceptre.resolvers.sub import Sub


class FirstResolver(Resolver):
    def resolve(self):
        return "first"


class SecondResolver(Resolver):
    def resolve(self):
        return "second"


class TestSub:
    def test_resolve__combines_resolvers_into_single_string(self):
        argument = [
            "{first} is {first_value}; {second} is {second_value}",
            {
                "first": FirstResolver(),
                "second": SecondResolver(),
                "first_value": 123,
                "second_value": 456,
            },
        ]
        sub = Sub(argument, Mock())
        resolved = sub.resolve()
        expected = "first is 123; second is 456"
        assert expected == resolved

    @pytest.mark.parametrize(
        "bad_argument",
        [
            pytest.param("just a string", id="just a string"),
            pytest.param([123, {"something": "else"}], id="first item is not string"),
            pytest.param(["123", "hello"], id="second item is not a dict"),
            pytest.param(
                ["{this}", {"that": "hi"}], id="format string requires key not in dict"
            ),
            pytest.param(["first", ["second"], "third"], id="too many items"),
        ],
    )
    def test_resolve__invalid_arguments__raises_invalid_resolver_argument_error(
        self, bad_argument
    ):
        sub = Sub(bad_argument, Mock())
        with pytest.raises(InvalidResolverArgumentError):
            sub.resolve()
