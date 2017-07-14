# -*- coding: utf-8 -*-

import os

import pytest


@pytest.fixture(scope="session")
def fixtures_dir():
    """
    Returns the absolute path to the fixtures directory.

    Located at <sceptre_root>/tests/fixtures

    :returns: Path to the fixtures directory.
    :rtype: str
    """
    test_dir = os.path.dirname(__file__)
    fixtures_dir = os.path.join(test_dir, "fixtures")
    return fixtures_dir
