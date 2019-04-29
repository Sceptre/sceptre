# -*- coding: utf-8 -*-

import importlib
from mock import sentinel, MagicMock

from sceptre.stack import Stack
from sceptre.template import Template


class TestStack(object):

    def setup_method(self, test_method):
        self.stack = Stack(
            name='dev/app/stack', project_code=sentinel.project_code,
            template_bucket_name=sentinel.template_bucket_name,
            template_key_prefix=sentinel.template_key_prefix,
            required_version=sentinel.required_version,
            template_path=sentinel.template_path, region=sentinel.region,
            profile=sentinel.profile, parameters={"key1": "val1"},
            sceptre_user_data=sentinel.sceptre_user_data, hooks={},
            s3_details=None, dependencies=sentinel.dependencies,
            role_arn=sentinel.role_arn, protected=False,
            tags={"tag1": "val1"}, external_name=sentinel.external_name,
            notifications=[sentinel.notification],
            on_failure=sentinel.on_failure,
            stack_timeout=sentinel.stack_timeout,
            stack_group_config={}
        )
        self.stack._template = MagicMock(spec=Template)

    def test_initiate_stack(self):
        stack = Stack(
            name='dev/stack/app', project_code=sentinel.project_code,
            template_path=sentinel.template_path,
            template_bucket_name=sentinel.template_bucket_name,
            template_key_prefix=sentinel.template_key_prefix,
            required_version=sentinel.required_version,
            region=sentinel.region, external_name=sentinel.external_name
        )
        assert stack.name == 'dev/stack/app'
        assert stack.project_code == sentinel.project_code
        assert stack.template_bucket_name == sentinel.template_bucket_name
        assert stack.template_key_prefix == sentinel.template_key_prefix
        assert stack.required_version == sentinel.required_version
        assert stack.external_name == sentinel.external_name
        assert stack.hooks == {}
        assert stack.parameters == {}
        assert stack.sceptre_user_data == {}
        assert stack.template_path == sentinel.template_path
        assert stack.s3_details is None
        assert stack._template is None
        assert stack.protected is False
        assert stack.role_arn is None
        assert stack.dependencies == []
        assert stack.tags == {}
        assert stack.notifications == []
        assert stack.on_failure is None
        assert stack.stack_group_config == {}

    def test_stack_repr(self):
        assert self.stack.__repr__() == \
            "sceptre.stack.Stack(" \
            "name='dev/app/stack', " \
            "project_code=sentinel.project_code, " \
            "template_path=sentinel.template_path, " \
            "region=sentinel.region, " \
            "template_bucket_name=sentinel.template_bucket_name, "\
            "template_key_prefix=sentinel.template_key_prefix, "\
            "required_version=sentinel.required_version, "\
            "profile=sentinel.profile, " \
            "sceptre_user_data=sentinel.sceptre_user_data, " \
            "parameters={'key1': 'val1'}, "\
            "hooks={}, "\
            "s3_details=None, " \
            "dependencies=sentinel.dependencies, "\
            "role_arn=sentinel.role_arn, "\
            "protected=False, "\
            "tags={'tag1': 'val1'}, "\
            "external_name=sentinel.external_name, " \
            "notifications=[sentinel.notification], " \
            "on_failure=sentinel.on_failure, " \
            "stack_timeout=sentinel.stack_timeout, " \
            "stack_group_config={}" \
            ")"

    def test_repr_can_eval_correctly(self):
        sceptre = importlib.import_module('sceptre')
        mock = importlib.import_module('mock')
        evaluated_stack = eval(
            repr(self.stack),
            {
                'sceptre': sceptre,
                'sentinel': mock.mock.sentinel
            }
        )
        assert isinstance(evaluated_stack, Stack)
        assert evaluated_stack.__eq__(self.stack)
