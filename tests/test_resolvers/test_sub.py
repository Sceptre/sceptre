from unittest.mock import Mock

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
