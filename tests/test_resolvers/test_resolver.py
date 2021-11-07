# -*- coding: utf-8 -*-
from unittest.mock import call

import pytest
from mock import sentinel, MagicMock

from sceptre.resolvers import (
    Resolver,
    ResolvableContainerProperty,
    RecursiveResolve
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
    resolvable_container_property = ResolvableContainerProperty("resolvable_container_property")
    config = MagicMock()


class TestResolver(object):

    def setup_method(self, test_method):
        self.mock_resolver = MockResolver(
            argument=sentinel.argument,
            stack=sentinel.stack
        )

    def test_init(self):
        assert self.mock_resolver.stack == sentinel.stack
        assert self.mock_resolver.argument == sentinel.argument


class TestResolvableContainerPropertyDescriptor(object):

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
                [
                    [
                        mock_resolver,
                        "String",
                        None
                    ],
                    mock_resolver,
                    "String"
                ]
            ]
        ]

        cloned_data_structure = [
            "String",
            mock_resolver.clone.return_value,
            [
                mock_resolver.clone.return_value,
                "String",
                [
                    [
                        mock_resolver.clone.return_value,
                        "String",
                        None
                    ],
                    mock_resolver.clone.return_value,
                    "String"
                ]
            ]
        ]

        self.mock_object.resolvable_container_property = complex_data_structure
        assert self.mock_object._resolvable_container_property == cloned_data_structure
        expected_calls = [
            call(self.mock_object),
            call().setup()
        ] * 4
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
                [
                    [
                        mock_resolver,
                        "String",
                        None
                    ],
                    mock_resolver,
                    "String"
                ],
                None
            ],
            None
        ]

        resolved_complex_data_structure = [
            "String",
            "Resolved",
            [
                "Resolved",
                "String",
                [
                    [
                        "Resolved",
                        "String",
                        None
                    ],
                    "Resolved",
                    "String"
                ],
                None
            ],
            None
        ]

        self.mock_object._resolvable_container_property = complex_data_structure
        prop = self.mock_object.resolvable_container_property
        assert prop == resolved_complex_data_structure

    def test_getting_resolvable_property_with_nested_dictionaries_and_lists(
        self
    ):
        mock_resolver = MagicMock(spec=MockResolver)
        mock_resolver.resolve.return_value = "Resolved"

        complex_data_structure = {
            "String": "String",
            "None": None,
            "Resolver": mock_resolver,
            "List": [
                    [
                        mock_resolver,
                        "String",
                        None
                    ],
                    {
                        "Dictionary": {},
                        "String": "String",
                        "None": None,
                        "Resolver": mock_resolver,
                        "List": [
                            mock_resolver
                        ]
                    },
                    mock_resolver,
                    "String"
            ],
            "Dictionary": {
                "Resolver": mock_resolver,
                "Dictionary": {
                    "List": [
                        [
                            mock_resolver,
                            "String",
                            None
                        ],
                        mock_resolver,
                        "String"
                    ],
                    "String": "String",
                    "None": None,
                    "Resolver": mock_resolver
                },
                "String": "String",
                "None": None
            }
        }

        resolved_complex_data_structure = {
            "String": "String",
            "None": None,
            "Resolver": "Resolved",
            "List": [
                    [
                        "Resolved",
                        "String",
                        None
                    ],
                    {
                        "Dictionary": {},
                        "String": "String",
                        "None": None,
                        "Resolver": "Resolved",
                        "List": [
                            "Resolved"
                        ]
                    },
                    "Resolved",
                    "String"
            ],
            "Dictionary": {
                "Resolver": "Resolved",
                "Dictionary": {
                    "List": [
                        [
                            "Resolved",
                            "String",
                            None
                        ],
                        "Resolved",
                        "String"
                    ],
                    "String": "String",
                    "None": None,
                    "Resolver": "Resolved"
                },
                "String": "String",
                "None": None
            }
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
                    "Resolver": mock_resolver
                },
                "String": "String",
                "None": None
            }
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
                    "Resolver": "Resolved"
                },
                "String": "String",
                "None": None
            }
        }

        self.mock_object._resolvable_container_property = complex_data_structure
        prop = self.mock_object.resolvable_container_property
        assert prop == resolved_complex_data_structure

    def test_get__resolver_references_same_property_for_other_value__resolves_it(self):
        class MyResolver(Resolver):
            def resolve(self):
                return self.stack.resolvable_container_property['other_value']

        resolver = MyResolver()
        self.mock_object.resolvable_container_property = {
            'other_value': 'abc',
            'resolver': resolver
        }

        assert self.mock_object.resolvable_container_property['resolver'] == 'abc'

    def test_get__resolver_references_itself__raises_recursive_resolve(self):
        class RecursiveResolver(Resolver):
            def resolve(self):
                return self.stack.resolvable_container_property['resolver']

        resolver = RecursiveResolver()
        self.mock_object.resolvable_container_property = {
            'resolver': resolver
        }
        with pytest.raises(RecursiveResolve):
            self.mock_object.resolvable_container_property

    def test_get__resolvable_container_property_references_same_property_of_other_stack__resolves(self):
        stack1 = MockClass()
        stack1.resolvable_container_property = {
            'testing': 'stack1'
        }

        class OtherStackResolver(Resolver):
            def resolve(self):
                return stack1.resolvable_container_property['testing']

        stack2 = MockClass()
        stack2.resolvable_container_property = {
            'resolver': OtherStackResolver()
        }

        assert stack2.resolvable_container_property == {
            'resolver': 'stack1'
        }
