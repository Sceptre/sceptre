import pytest

from sceptre.resolvers import are_placeholders_enabled, Resolver
from sceptre.resolvers.placeholders import (
    use_resolver_placeholders_on_error,
    PlaceholderType,
    create_placeholder_value,
)


class TestPlaceholders:
    def test_are_placeholders_enabled__returns_false(self):
        assert are_placeholders_enabled() is False

    def test_are_placeholders_enabled__in_placeholder_context__returns_true(self):
        with use_resolver_placeholders_on_error():
            assert are_placeholders_enabled() is True

    def test_are_placeholders_enabled__out_of_placeholder_context__returns_false(self):
        with use_resolver_placeholders_on_error():
            pass

        assert are_placeholders_enabled() is False

    def test_are_placeholders_enabled__error_in_placeholder_context__returns_false(
        self,
    ):
        with pytest.raises(ValueError), use_resolver_placeholders_on_error():
            raise ValueError()

        assert are_placeholders_enabled() is False

    @pytest.mark.parametrize(
        "placeholder_type,argument,expected",
        [
            pytest.param(
                PlaceholderType.explicit,
                None,
                "{ !MyResolver }",
                id="explicit no argument",
            ),
            pytest.param(
                PlaceholderType.explicit,
                "argument",
                "{ !MyResolver(argument) }",
                id="explicit string argument",
            ),
            pytest.param(
                PlaceholderType.explicit,
                {"key": "value"},
                "{ !MyResolver({'key': 'value'}) }",
                id="explicit dict argument",
            ),
            pytest.param(
                PlaceholderType.alphanum, None, "MyResolver", id="alphanum no argument"
            ),
            pytest.param(
                PlaceholderType.alphanum,
                "argument",
                "MyResolverargument",
                id="alphanum string argument",
            ),
            pytest.param(
                PlaceholderType.alphanum,
                {"key": "value"},
                "MyResolverkeyvalue",
                id="alphanum dict argument",
            ),
            pytest.param(PlaceholderType.none, "something", None),
        ],
    )
    def test_create_placeholder_value(self, placeholder_type, argument, expected):
        class MyResolver(Resolver):
            def resolve(self):
                pass

        resolver = MyResolver(argument)

        with use_resolver_placeholders_on_error():
            result = create_placeholder_value(resolver, placeholder_type)

        assert result == expected
