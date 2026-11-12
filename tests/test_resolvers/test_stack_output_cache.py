"""Tests for the cache of Stack outputs that all resolvers share (#1601)."""

from unittest.mock import MagicMock

import pytest

from sceptre.resolvers.stack_output import StackOutput, StackOutputBase


@pytest.fixture(autouse=True)
def clear_shared_cache():
    # Only exists with the fix. A shared cache must start empty for each test.
    if hasattr(StackOutputBase, "clear_cache"):
        StackOutputBase.clear_cache()


def _dependency_stack():
    stack = MagicMock()
    stack.name = "shared/vpc"
    stack.project_code = "project"
    stack.profile = None
    stack.region = "eu-west-1"
    stack.sceptre_role = None
    stack.connection_manager.call.return_value = {
        "Stacks": [{"Outputs": [{"OutputKey": "VpcId", "OutputValue": "vpc-1"}]}]
    }
    return stack


def _resolver(dependency, stack):
    # The same construction as the config reader: one resolver per tag,
    # setup() adds the dependency, resolve() reads the output.
    resolver = StackOutput("shared/vpc.yaml::VpcId", stack)
    resolver.setup()
    stack.dependencies = [dependency]
    return resolver


def test_one_resolver_fetches_one_time():
    dependency = _dependency_stack()
    stack = MagicMock(connection_manager=dependency.connection_manager)
    stack.dependencies = []
    resolver = _resolver(dependency, stack)
    for _ in range(5):
        assert resolver.resolve() == "vpc-1"
    assert dependency.connection_manager.call.call_count == 1


def test_ten_stacks_that_read_the_same_output_fetch_one_time():
    dependency = _dependency_stack()
    resolvers = []
    for _ in range(10):
        stack = MagicMock(connection_manager=dependency.connection_manager)
        stack.dependencies = []
        resolvers.append(_resolver(dependency, stack))
    for resolver in resolvers:
        assert resolver.resolve() == "vpc-1"
    assert dependency.connection_manager.call.call_count == 1
