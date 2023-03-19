from unittest.mock import Mock

import pytest

from sceptre.exceptions import InvalidResolverArgumentError
from sceptre.resolvers import Resolver
from sceptre.resolvers.join import Join


class ArgResolver(Resolver):
    def resolve(self):
        return self.argument


class TestJoin:
    def test_resolve__joins_resolver_values_into_single_string(self):
        argument = [
            "/",
            [
                ArgResolver("first"),
                "middle",
                ArgResolver("last"),
            ],
        ]
        join = Join(argument, Mock())
        resolved = join.resolve()
        expected = "first/middle/last"
        assert expected == resolved

    def test_resolve__argument_returns_non_string__casts_it_to_string(self):
        argument = [
            "/",
            [
                ArgResolver(123),
                "other",
            ],
        ]
        join = Join(argument, Mock())
        resolved = join.resolve()
        expected = "123/other"
        assert expected == resolved

    def test_resolve__argument_returns_none__not_included_in_string(self):
        argument = [
            "/",
            [
                ArgResolver("first"),
                ArgResolver(None),
                ArgResolver("last"),
            ],
        ]
        join = Join(argument, Mock())
        resolved = join.resolve()
        expected = "first/last"
        assert expected == resolved

    @pytest.mark.parametrize(
        "bad_argument",
        [
            pytest.param("just a string", id="just a string"),
            pytest.param([123, ["something"]], id="non-string delimiter"),
            pytest.param(
                ["join", "not list to join"], id="second argument is not list"
            ),
            pytest.param(["first", ["second"], "third"], id="too many items"),
        ],
    )
    def test_resolve__invalid_arguments_passed__raises_invalid_resolver_argument_error(
        self, bad_argument
    ):
        join = Join(bad_argument, Mock())
        with pytest.raises(InvalidResolverArgumentError):
            join.resolve()
