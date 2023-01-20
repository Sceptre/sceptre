# -*- coding: utf-8 -*-
from unittest.mock import call, Mock

import pytest
from unittest.mock import sentinel, MagicMock

from sceptre.resolvers import (
    Resolver,
    ResolvableContainerProperty,
    ResolvableValueProperty,
    RecursiveResolve,
)
from sceptre.resolvers.placeholders import (
    use_resolver_placeholders_on_error,
    create_placeholder_value,
    PlaceholderType,
)


class MockResolver(Resolver):
    """
    MockResolver inherits from the abstract base class Resolver, and
    implements the abstract methods. It is used to allow testing on
    Resolver, which is not otherwise instantiable.
    """

    def resolve(self):
        pass


class MockClass(object):
    resolvable_container_property = ResolvableContainerProperty(
        "resolvable_container_property"
    )
    container_with_alphanum_placeholder = ResolvableContainerProperty(
        "container_with_placeholder_override", PlaceholderType.alphanum
    )
    resolvable_value_property = ResolvableValueProperty("resolvable_value_property")
    value_with_none_placeholder = ResolvableValueProperty(
        "value_with_placeholder_override", PlaceholderType.none
    )
    config = MagicMock()


class TestResolver(object):
    def setup_method(self, test_method):
        self.mock_resolver = MockResolver(
            argument=sentinel.argument, stack=sentinel.stack
        )

    def test_init(self):
        assert self.mock_resolver.stack == sentinel.stack
        assert self.mock_resolver.argument == sentinel.argument


class TestResolvableContainerPropertyDescriptor:
    def setup_method(self, test_method):
        self.mock_object = MockClass()

    def test_setting_resolvable_property_with_none(self):
        self.mock_object.resolvable_container_property = None
        assert self.mock_object._resolvable_container_property is None

    def test_setting_resolvable_property_with_nested_lists(self):
        mock_resolver = MagicMock(spec=MockResolver)

        complex_data_structure = [
            "String",
            mock_resolver,
            [
                mock_resolver,
                "String",
                [[mock_resolver, "String", None], mock_resolver, "String"],
            ],
        ]

        cloned_data_structure = [
            "String",
            mock_resolver.clone.return_value,
            [
                mock_resolver.clone.return_value,
                "String",
                [
                    [mock_resolver.clone.return_value, "String", None],
                    mock_resolver.clone.return_value,
                    "String",
                ],
            ],
        ]

        self.mock_object.resolvable_container_property = complex_data_structure
        assert self.mock_object._resolvable_container_property == cloned_data_structure
        expected_calls = [call(self.mock_object), call().setup()] * 4
        mock_resolver.clone.assert_has_calls(expected_calls)

    def test_getting_resolvable_property_with_none(self):
        self.mock_object._resolvable_container_property = None
        assert self.mock_object.resolvable_container_property is None

    def test_getting_resolvable_property_with_nested_lists(self):
        mock_resolver = MagicMock(spec=MockResolver)
        mock_resolver.resolve.return_value = "Resolved"

        complex_data_structure = [
            "String",
            mock_resolver,
            [
                mock_resolver,
                "String",
                [[mock_resolver, "String", None], mock_resolver, "String"],
                None,
            ],
            None,
        ]

        resolved_complex_data_structure = [
            "String",
            "Resolved",
            [
                "Resolved",
                "String",
                [["Resolved", "String", None], "Resolved", "String"],
                None,
            ],
            None,
        ]

        self.mock_object._resolvable_container_property = complex_data_structure
        prop = self.mock_object.resolvable_container_property
        assert prop == resolved_complex_data_structure

    def test_getting_resolvable_property_with_nested_dictionaries_and_lists(self):
        mock_resolver = MagicMock(spec=MockResolver)
        mock_resolver.resolve.return_value = "Resolved"

        complex_data_structure = {
            "String": "String",
            "None": None,
            "Resolver": mock_resolver,
            "List": [
                [mock_resolver, "String", None],
                {
                    "Dictionary": {},
                    "String": "String",
                    "None": None,
                    "Resolver": mock_resolver,
                    "List": [mock_resolver],
                },
                mock_resolver,
                "String",
            ],
            "Dictionary": {
                "Resolver": mock_resolver,
                "Dictionary": {
                    "List": [[mock_resolver, "String", None], mock_resolver, "String"],
                    "String": "String",
                    "None": None,
                    "Resolver": mock_resolver,
                },
                "String": "String",
                "None": None,
            },
        }

        resolved_complex_data_structure = {
            "String": "String",
            "None": None,
            "Resolver": "Resolved",
            "List": [
                ["Resolved", "String", None],
                {
                    "Dictionary": {},
                    "String": "String",
                    "None": None,
                    "Resolver": "Resolved",
                    "List": ["Resolved"],
                },
                "Resolved",
                "String",
            ],
            "Dictionary": {
                "Resolver": "Resolved",
                "Dictionary": {
                    "List": [["Resolved", "String", None], "Resolved", "String"],
                    "String": "String",
                    "None": None,
                    "Resolver": "Resolved",
                },
                "String": "String",
                "None": None,
            },
        }

        self.mock_object._resolvable_container_property = complex_data_structure
        prop = self.mock_object.resolvable_container_property
        assert prop == resolved_complex_data_structure

    def test_getting_resolvable_property_with_nested_dictionaries(self):
        mock_resolver = MagicMock(spec=MockResolver)
        mock_resolver.resolve.return_value = "Resolved"

        complex_data_structure = {
            "String": "String",
            "None": None,
            "Resolver": mock_resolver,
            "Dictionary": {
                "Resolver": mock_resolver,
                "Dictionary": {
                    "Dictionary": {},
                    "String": "String",
                    "None": None,
                    "Resolver": mock_resolver,
                },
                "String": "String",
                "None": None,
            },
        }

        resolved_complex_data_structure = {
            "String": "String",
            "None": None,
            "Resolver": "Resolved",
            "Dictionary": {
                "Resolver": "Resolved",
                "Dictionary": {
                    "Dictionary": {},
                    "String": "String",
                    "None": None,
                    "Resolver": "Resolved",
                },
                "String": "String",
                "None": None,
            },
        }

        self.mock_object._resolvable_container_property = complex_data_structure
        prop = self.mock_object.resolvable_container_property
        assert prop == resolved_complex_data_structure

    def test_get__resolver_references_same_property_for_other_value__resolves_it(self):
        class MyResolver(Resolver):
            def resolve(self):
                return self.stack.resolvable_container_property["other_value"]

        resolver = MyResolver()
        self.mock_object.resolvable_container_property = {
            "other_value": "abc",
            "resolver": resolver,
        }

        assert self.mock_object.resolvable_container_property["resolver"] == "abc"

    def test_get__resolver_references_itself__raises_recursive_resolve(self):
        class RecursiveResolver(Resolver):
            def resolve(self):
                return self.stack.resolvable_container_property["resolver"]

        resolver = RecursiveResolver()
        self.mock_object.resolvable_container_property = {"resolver": resolver}
        with pytest.raises(RecursiveResolve):
            self.mock_object.resolvable_container_property

    def test_get__resolvable_container_property_references_same_property_of_other_stack__resolves(
        self,
    ):
        stack1 = MockClass()
        stack1.resolvable_container_property = {"testing": "stack1"}

        class OtherStackResolver(Resolver):
            def resolve(self):
                return stack1.resolvable_container_property["testing"]

        stack2 = MockClass()
        stack2.resolvable_container_property = {"resolver": OtherStackResolver()}

        assert stack2.resolvable_container_property == {"resolver": "stack1"}

    def test_get__resolver_resolves_to_none__value_is_dict__deletes_those_items_from_dict(
        self,
    ):
        class MyResolver(Resolver):
            def resolve(self):
                return None

        resolver = MyResolver()
        self.mock_object.resolvable_container_property = {
            "a": 4,
            "b": resolver,
            "c": 3,
            "d": resolver,
            "e": resolver,
            "f": 5,
        }
        expected = {"a": 4, "c": 3, "f": 5}
        assert self.mock_object.resolvable_container_property == expected

    def test_get__resolver_resolves_to_none__value_is_dict__deletes_those_items_from_complex_structure(
        self,
    ):
        class MyResolver(Resolver):
            def resolve(self):
                return None

        resolver = MyResolver()
        self.mock_object.resolvable_container_property = {
            "a": 4,
            "b": [
                resolver,
            ],
            "c": [{"v": resolver}],
            "d": 3,
        }
        expected = {"a": 4, "b": [], "c": [{}], "d": 3}
        assert self.mock_object.resolvable_container_property == expected

    def test_get__resolver_resolves_to_none__value_is_list__deletes_that_item_from_list(
        self,
    ):
        class MyResolver(Resolver):
            def resolve(self):
                return None

        resolver = MyResolver()
        self.mock_object.resolvable_container_property = [1, resolver, 3]
        expected = [1, 3]
        assert self.mock_object.resolvable_container_property == expected

    def test_get__resolver_resolves_to_none__value_is_dict__deletes_that_key_from_dict(
        self,
    ):
        class MyResolver(Resolver):
            def resolve(self):
                return None

        resolver = MyResolver()
        self.mock_object.resolvable_container_property = {
            "some key": "some value",
            "resolver": resolver,
        }
        expected = {"some key": "some value"}
        assert self.mock_object.resolvable_container_property == expected

    def test_get__resolvers_resolves_to_none__value_is_list__deletes_those_items_from_list(
        self,
    ):
        class MyResolver(Resolver):
            def resolve(self):
                return None

        resolver = MyResolver()

        self.mock_object.resolvable_container_property = [
            1,
            resolver,
            3,
            resolver,
            resolver,
            6,
        ]
        expected = [1, 3, 6]
        assert self.mock_object.resolvable_container_property == expected

    def test_get__resolvers_resolves_to_none__value_is_list__deletes_all_items_from_list(
        self,
    ):
        class MyResolver(Resolver):
            def resolve(self):
                return None

        resolver = MyResolver()

        self.mock_object.resolvable_container_property = [resolver, resolver, resolver]
        expected = []
        assert self.mock_object.resolvable_container_property == expected

    def test_get__value_in_list_is_none__returns_list_with_none(self):
        self.mock_object.resolvable_container_property = [1, None, 3]
        expected = [1, None, 3]
        assert self.mock_object.resolvable_container_property == expected

    def test_get__value_in_dict_is_none__returns_dict_with_none(self):
        self.mock_object.resolvable_container_property = {
            "some key": "some value",
            "none key": None,
        }
        expected = {"some key": "some value", "none key": None}
        assert self.mock_object.resolvable_container_property == expected

    def test_get__resolver_raises_error__placeholders_allowed__returns_placeholder(
        self,
    ):
        class ErroringResolver(Resolver):
            def resolve(self):
                raise ValueError()

        resolver = ErroringResolver()
        self.mock_object.resolvable_container_property = {"resolver": resolver}
        with use_resolver_placeholders_on_error():
            result = self.mock_object.resolvable_container_property

        assert result == {
            "resolver": create_placeholder_value(resolver, PlaceholderType.explicit)
        }

    def test_get__resolver_raises_error__placeholders_not_allowed__raises_error(self):
        class ErroringResolver(Resolver):
            def resolve(self):
                raise ValueError()

        resolver = ErroringResolver()
        self.mock_object.resolvable_container_property = {"resolver": resolver}
        with pytest.raises(ValueError):
            self.mock_object.resolvable_container_property

    def test_get__resolver_raises_recursive_resolve__placeholders_allowed__raises_error(
        self,
    ):
        class RecursiveResolver(Resolver):
            def resolve(self):
                raise RecursiveResolve()

        resolver = RecursiveResolver()
        self.mock_object.resolvable_container_property = {"resolver": resolver}
        with use_resolver_placeholders_on_error(), pytest.raises(RecursiveResolve):
            self.mock_object.resolvable_container_property

    def test_get__resolver_raises_error__placeholders_allowed__alternate_placeholder_type__uses_alternate(
        self,
    ):
        class ErroringResolver(Resolver):
            def resolve(self):
                raise ValueError()

        resolver = ErroringResolver()
        self.mock_object.container_with_alphanum_placeholder = {"resolver": resolver}
        with use_resolver_placeholders_on_error():
            result = self.mock_object.container_with_alphanum_placeholder

        assert result == {
            "resolver": create_placeholder_value(resolver, PlaceholderType.alphanum)
        }


class TestResolvableValueProperty:
    def setup_method(self, test_method):
        self.mock_object = MockClass()

    @pytest.mark.parametrize("value", ["string", True, 123, 1.23, None])
    def test_set__non_resolver__sets_private_variable_as_value(self, value):
        self.mock_object.resolvable_value_property = value
        assert self.mock_object._resolvable_value_property == value

    def test_set__resolver__sets_private_variable_with_clone_of_resolver_with_instance(
        self,
    ):
        resolver = Mock(spec=MockResolver)
        self.mock_object.resolvable_value_property = resolver
        assert (
            self.mock_object._resolvable_value_property == resolver.clone.return_value
        )

    def test_set__resolver__sets_up_cloned_resolver(self):
        resolver = Mock(spec=MockResolver)
        self.mock_object.resolvable_value_property = resolver
        resolver.clone.return_value.setup.assert_any_call()

    @pytest.mark.parametrize("value", ["string", True, 123, 1.23, None])
    def test_get__non_resolver__returns_value(self, value):
        self.mock_object._resolvable_value_property = value
        assert self.mock_object.resolvable_value_property == value

    def test_get__resolver__returns_resolved_value(self):
        resolver = Mock(spec=MockResolver)
        self.mock_object._resolvable_value_property = resolver
        assert (
            self.mock_object.resolvable_value_property == resolver.resolve.return_value
        )

    def test_get__resolver__updates_set_value_with_resolved_value(self):
        resolver = Mock(spec=MockResolver)
        self.mock_object._resolvable_value_property = resolver
        self.mock_object.resolvable_value_property
        assert (
            self.mock_object._resolvable_value_property == resolver.resolve.return_value
        )

    def test_get__resolver__resolver_attempts_to_access_resolver__raises_recursive_resolve(
        self,
    ):
        class RecursiveResolver(Resolver):
            def resolve(self):
                # This should blow up!
                self.stack.resolvable_value_property

        resolver = RecursiveResolver()
        self.mock_object.resolvable_value_property = resolver

        with pytest.raises(RecursiveResolve):
            self.mock_object.resolvable_value_property

    def test_get__resolvable_value_property_references_same_property_of_other_stack__resolves(
        self,
    ):
        stack1 = MockClass()
        stack1.resolvable_value_property = "stack1"

        class OtherStackResolver(Resolver):
            def resolve(self):
                return stack1.resolvable_value_property

        stack2 = MockClass()
        stack2.resolvable_value_property = OtherStackResolver()

        assert stack2.resolvable_value_property == "stack1"

    def test_get__resolver_raises_error__placeholders_allowed__returns_placeholder(
        self,
    ):
        class ErroringResolver(Resolver):
            def resolve(self):
                raise ValueError()

        resolver = ErroringResolver()
        self.mock_object.resolvable_value_property = resolver
        with use_resolver_placeholders_on_error():
            result = self.mock_object.resolvable_value_property

        assert result == create_placeholder_value(resolver, PlaceholderType.explicit)

    def test_get__resolver_raises_error__placeholders_not_allowed__raises_error(self):
        class ErroringResolver(Resolver):
            def resolve(self):
                raise ValueError()

        resolver = ErroringResolver()
        self.mock_object.resolvable_value_property = resolver
        with pytest.raises(ValueError):
            self.mock_object.resolvable_value_property

    def test_get__resolver_raises_recursive_resolve__placeholders_allowed__raises_error(
        self,
    ):
        class RecursiveResolver(Resolver):
            def resolve(self):
                raise RecursiveResolve()

        resolver = RecursiveResolver()
        self.mock_object.resolvable_value_property = resolver
        with use_resolver_placeholders_on_error(), pytest.raises(RecursiveResolve):
            self.mock_object.resolvable_value_property

    def test_get__resolver_raises_error__placeholders_allowed__alternate_placeholder_type__uses_alternate_type(
        self,
    ):
        class ErroringResolver(Resolver):
            def resolve(self):
                raise ValueError()

        resolver = ErroringResolver()
        self.mock_object.value_with_none_placeholder = resolver
        with use_resolver_placeholders_on_error():
            result = self.mock_object.value_with_none_placeholder

        assert result == create_placeholder_value(resolver, PlaceholderType.none)
