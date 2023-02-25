from unittest.mock import Mock

from sceptre.resolvers import Resolver
from sceptre.resolvers.join import Join


class FirstResolver(Resolver):
    def resolve(self):
        return "first"


class SecondResolver(Resolver):
    def resolve(self):
        return "last"


class TestJoin:
    def test_resolve__joines_resolver_values_into_single_string(self):
        argument = [
            "/",
            [
                FirstResolver(),
                "middle",
                SecondResolver(),
            ],
        ]
        join = Join(argument, Mock())
        resolved = join.resolve()
        expected = "first/middle/last"
        assert expected == resolved
