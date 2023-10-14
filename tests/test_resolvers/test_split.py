from unittest.mock import Mock

import pytest

from sceptre.exceptions import InvalidResolverArgumentError
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

    @pytest.mark.parametrize(
        "bad_argument",
        [
            pytest.param("just a string", id="just a string"),
            pytest.param([123, "something"], id="first item is not string"),
            pytest.param(["something", 123], id="second item is not string"),
        ],
    )
    def test_resolve__invalid_arguments__raises_invalid_resolver_argument_error(
        self, bad_argument
    ):
        split = Split(bad_argument, Mock())
        with pytest.raises(InvalidResolverArgumentError):
            split.resolve()
