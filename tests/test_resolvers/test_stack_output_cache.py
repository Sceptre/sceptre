"""Tests for the cache of Stack outputs that all resolvers share (#1601)."""

from unittest.mock import MagicMock

import pytest

from sceptre.resolvers.stack_output import StackOutput, StackOutputBase


class CacheProbe(StackOutputBase):
    def resolve(self):
        return None


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


def test_stacks_with_different_connection_defaults_do_not_share_an_entry():
    # stack_output_external without a profile passes (None, None, None), which
    # ConnectionManager.call reads as the defaults of the resolving Stack.
    managers = []
    for profile in ("account-a", "account-b"):
        manager = MagicMock()
        manager.profile = profile
        manager.region = "eu-west-1"
        manager.sceptre_role = None
        manager.call.return_value = {
            "Stacks": [{"Outputs": [{"OutputKey": "Id", "OutputValue": profile}]}]
        }
        managers.append(manager)
    resolvers = []
    for manager in managers:
        stack = MagicMock(connection_manager=manager)
        resolvers.append(CacheProbe(None, stack))

    outputs = [r._get_stack_outputs("shared-name") for r in resolvers]

    assert outputs == [{"Id": "account-a"}, {"Id": "account-b"}]
    assert all(m.call.call_count == 1 for m in managers)


def test_fetches_of_different_stacks_run_in_parallel():
    import threading

    dependency = _dependency_stack()
    stack = MagicMock(connection_manager=dependency.connection_manager)
    resolver = CacheProbe(None, stack)
    slow_started = threading.Event()
    fast_finished = threading.Event()

    waited = {}

    def fetch(service, command, kwargs, **extra):
        if kwargs["StackName"] == "slow":
            slow_started.set()
            # Waits for the fetch of the other Stack. With one lock around
            # every fetch, that one never starts and the wait times out.
            waited["fast_finished"] = fast_finished.wait(timeout=5)
        return {"Stacks": [{"Outputs": []}]}

    dependency.connection_manager.call.side_effect = fetch
    slow = threading.Thread(
        target=resolver._get_stack_outputs, args=("slow",), kwargs={"profile": "p"}
    )
    slow.start()
    assert slow_started.wait(timeout=5)
    resolver._get_stack_outputs("fast", profile="p")
    fast_finished.set()
    slow.join(timeout=5)

    assert not slow.is_alive()
    assert waited == {"fast_finished": True}
    assert dependency.connection_manager.call.call_count == 2


def test_a_fetch_that_resolves_another_stack_on_the_same_thread_returns():
    # A sceptre_role given as a stack_output is resolved while the connection
    # manager is created, inside the fetch of another Stack. A lock held
    # around the fetch that is not reentrant blocks that thread forever.
    import threading

    dependency = _dependency_stack()
    stack = MagicMock(connection_manager=dependency.connection_manager)
    resolver = CacheProbe(None, stack)
    inner = {"done": False}
    results = {}

    def fetch(service, command, kwargs, **extra):
        if kwargs["StackName"] == "outer" and not inner["done"]:
            inner["done"] = True
            resolver._get_stack_outputs("inner", profile="p", region="r")
            resolver._get_stack_outputs("outer", profile="p", region="r")
        return {
            "Stacks": [
                {"Outputs": [{"OutputKey": "K", "OutputValue": kwargs["StackName"]}]}
            ]
        }

    dependency.connection_manager.call.side_effect = fetch
    worker = threading.Thread(
        target=lambda: results.update(
            outer=resolver._get_stack_outputs("outer", profile="p", region="r")
        ),
        daemon=True,
    )
    worker.start()
    worker.join(timeout=5)

    assert not worker.is_alive()
    assert results == {"outer": {"K": "outer"}}
    assert resolver._get_stack_outputs("inner", profile="p", region="r") == {
        "K": "inner"
    }
    # outer, inner, and the re-entrant outer.
    assert dependency.connection_manager.call.call_count == 3


def test_a_resolver_that_waits_for_a_fetch_in_progress_reads_the_result():
    import threading

    dependency = _dependency_stack()
    stack = MagicMock(connection_manager=dependency.connection_manager)
    resolver = CacheProbe(None, stack)
    fetch_started = threading.Event()
    release_fetch = threading.Event()

    def fetch(service, command, kwargs, **extra):
        fetch_started.set()
        release_fetch.wait(timeout=5)
        return {"Stacks": [{"Outputs": [{"OutputKey": "K", "OutputValue": "v"}]}]}

    dependency.connection_manager.call.side_effect = fetch
    results = []
    first = threading.Thread(
        target=lambda: results.append(resolver._get_stack_outputs("s", profile="p"))
    )
    second = threading.Thread(
        target=lambda: results.append(resolver._get_stack_outputs("s", profile="p"))
    )
    first.start()
    assert fetch_started.wait(timeout=5)
    second.start()
    release_fetch.set()
    first.join(timeout=5)
    second.join(timeout=5)

    assert results == [{"K": "v"}, {"K": "v"}]
    assert dependency.connection_manager.call.call_count == 1
