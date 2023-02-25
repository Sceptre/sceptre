from unittest.mock import Mock

from sceptre.resolvers import Resolver
from sceptre.resolvers.split import Split


class MyResolver(Resolver):
    def resolve(self):
        return "first,second,third"


class TestSplit:
    def test_resolve__splits_resolver_value_into_list(self):
        argument = [",", MyResolver()]
        split = Split(argument, Mock())
        resolved = split.resolve()
        expected = ["first", "second", "third"]
        assert expected == resolved
