# -*- coding: utf-8 -*-

from mock import sentinel

from sceptre.stack_group import StackGroup


class TestStackGroup(object):

    def setup_method(self, test_method):
        self.stack_group = StackGroup(
            path="path",
            options=sentinel.options
        )

        # Run the rest of the tests against a leaf stack_group
        self.stack_group._is_leaf = True

    def test_initialise_stack_group(self):
        assert self.stack_group.path == "path"
        assert self.stack_group._options == sentinel.options
        assert self.stack_group.stacks == []
        assert self.stack_group.sub_stack_groups == []

    def test_initialise_stack_group_with_no_options(self):
        stack_group = StackGroup(path="path")
        assert stack_group.path == "path"
        assert stack_group._options == {}
        assert stack_group.stacks == []
        assert stack_group.sub_stack_groups == []

    def test_repr(self):
        self.stack_group.path = "path"
        self.stack_group.project_path = "project_path"
        self.stack_group._options = {}
        response = self.stack_group.__repr__()
        assert response == \
            ("sceptre.stack_group.StackGroup(""path='path', options='{}')")
