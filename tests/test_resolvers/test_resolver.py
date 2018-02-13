# -*- coding: utf-8 -*-

from mock import sentinel, MagicMock

from sceptre.resolvers import Resolver, ResolvableProperty


class MockResolver(Resolver):
    """
    MockResolver inherits from the abstract base class Resolver, and
    implements the abstract methods. It is used to allow testing on
    Resolver, which is not otherwise instantiable.
    """

    def resolve(self):
        pass


class MockClass(object):
    resolvable_property = ResolvableProperty("resolvable_property")
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


class TestResolvablePropertyDescriptor(object):

    def setup_method(self, test_method):
        self.mock_object = MockClass()

    def test_setting_resolvable_property_with_none(self):
        self.mock_object.resolvable_property = None
        assert self.mock_object._resolvable_property is None

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

        self.mock_object.resolvable_property = complex_data_structure
        assert self.mock_object._resolvable_property == complex_data_structure
        assert mock_resolver.stack == self.mock_object

    def test_getting_resolvable_property_with_none(self):
        self.mock_object._resolvable_property = None
        assert self.mock_object.resolvable_property is None

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

        self.mock_object._resolvable_property = complex_data_structure
        prop = self.mock_object.resolvable_property
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

        self.mock_object._resolvable_property = complex_data_structure
        prop = self.mock_object.resolvable_property
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

        self.mock_object._resolvable_property = complex_data_structure
        prop = self.mock_object.resolvable_property
        assert prop == resolved_complex_data_structure
