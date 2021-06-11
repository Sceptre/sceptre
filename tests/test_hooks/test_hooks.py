# -*- coding: utf-8 -*-
from mock import MagicMock

from sceptre.hooks import Hook, HookProperty, add_stack_hooks, execute_hooks
from sceptre.plan.actions import StackActions
from sceptre.stack import Stack


class MockHook(Hook):
    def __init__(self, *args, **kwargs):
        super(MockHook, self).__init__(*args, **kwargs)

    def run(self):
        pass


class TestHooksFunctions(object):
    def setup_method(self, test_method):
        self.stack = MagicMock(spec=Stack)

    def test_add_stack_hooks(self):
        mock_hook_before = MagicMock(spec=Hook)
        mock_hook_after = MagicMock(spec=Hook)
        mock_object = MagicMock()

        mock_object.stack.hooks = {
            'before_mock_function': [mock_hook_before],
            'after_mock_function': [mock_hook_after]
        }

        def mock_function(self):
            assert mock_hook_before.run.call_count == 1
            assert mock_hook_after.run.call_count == 0

        mock_object.mock_function = mock_function
        mock_object.mock_function.__name__ = 'mock_function'

        add_stack_hooks(mock_object.mock_function)(mock_object)

        assert mock_hook_before.run.call_count == 1
        assert mock_hook_after.run.call_count == 1

    def test_execute_hooks_with_not_a_list(self):
        execute_hooks(None, self.stack)

    def test_execute_hooks_with_empty_list(self):
        execute_hooks([], self.stack)

    def test_execute_hooks_with_list_with_non_hook_objects(self):
        execute_hooks([None, "string", 1, True], self.stack)

    def test_execute_hooks_with_single_hook(self):
        hook = MagicMock(spec=Hook)
        execute_hooks([hook], self.stack)
        hook.run.called_once_with()

    def test_execute_hooks_with_multiple_hook(self):
        hook_1 = MagicMock(spec=Hook)
        hook_2 = MagicMock(spec=Hook)
        execute_hooks([hook_1, hook_2], self.stack)
        hook_1.run.called_once_with()
        hook_2.run.called_once_with()


class TestHook(object):
    def setup_method(self, test_method):
        self.hook = MockHook()

    def test_hook_inheritance(self):
        assert isinstance(self.hook, Hook)


class MockClass(object):
    hook_property = HookProperty("hook_property")
    config = MagicMock()


class TestHookPropertyDescriptor(object):

    def setup_method(self, test_method):
        self.mock_object = MockClass()

    def test_setting_hook_property(self):
        mock_hook = MagicMock(spec=MockHook)

        self.mock_object.hook_property = [mock_hook]
        assert self.mock_object._hook_property == [mock_hook]

    def test_getting_hook_property(self):
        self.mock_object._hook_property = self.mock_object
        assert self.mock_object.hook_property == self.mock_object


class MultipleHook(Hook):
    def __init__(self, *args, **kwargs):
        super(MultipleHook, self).__init__(*args, **kwargs)

    def run(self, stack):
        pass


class TestHooksMultipleConfig(object):
    def setup_method(self, test_method):
        pass

    def test_add_stack_hooks(self):
        sub_stack_one = MagicMock(spec=StackActions)
        sub_stack_one.stack = MagicMock(spec=Stack)
        sub_stack_one.name = 'sub_stack_one'
        sub_stack_two = MagicMock(spec=StackActions)
        sub_stack_two.stack = MagicMock(spec=Stack)
        sub_stack_two.name = 'sub_stack_two'
        hook_before = MagicMock(MultipleHook)
        hook_after = MagicMock(MultipleHook)

        sub_stack_one.stack.hooks = sub_stack_two.stack.hooks = {
            'before_mock_function': [hook_before],
            'after_mock_function': [hook_after]
        }

        def mock_function(self):
            pass

        sub_stack_one.mock_function = sub_stack_two.mock_function = mock_function
        sub_stack_one.mock_function.__name__ = sub_stack_two.mock_function.__name__ = 'mock_function'

        add_stack_hooks(sub_stack_one.mock_function)(sub_stack_one)
        hook_before.run.assert_called_with(sub_stack_one.stack)
        hook_after.run.assert_called_with(sub_stack_one.stack)

        add_stack_hooks(sub_stack_two.mock_function)(sub_stack_two)
        hook_before.run.assert_called_with(sub_stack_two.stack)
        hook_after.run.assert_called_with(sub_stack_two.stack)
