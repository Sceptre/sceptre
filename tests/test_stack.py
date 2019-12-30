# -*- coding: utf-8 -*-

import importlib

from mock import MagicMock, sentinel
from sceptre.resolvers import Resolver
from sceptre.stack import Stack
from sceptre.template import Template


def stack_factory(**kwargs):
    call_kwargs = {
        'name': 'dev/app/stack',
        'project_code': sentinel.project_code,
        'template_bucket_name': sentinel.template_bucket_name,
        'template_key_prefix': sentinel.template_key_prefix,
        'required_version': sentinel.required_version,
        'template_path': sentinel.template_path,
        'region': sentinel.region,
        'profile': sentinel.profile,
        'parameters': {"key1": "val1"},
        'sceptre_user_data': sentinel.sceptre_user_data,
        'hooks': {},
        's3_details': None,
        'dependencies': sentinel.dependencies,
        'role_arn': sentinel.role_arn,
        'protected': False,
        'tags': {"tag1": "val1"},
        'external_name': sentinel.external_name,
        'notifications': [sentinel.notification],
        'on_failure': sentinel.on_failure,
        'stack_timeout': sentinel.stack_timeout,
        'stack_group_config': {}
    }
    call_kwargs.update(kwargs)
    return Stack(**call_kwargs)


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
            on_failure=sentinel.on_failure, iam_role=sentinel.iam_role,
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
        assert stack.iam_role is None
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
            "iam_role=sentinel.iam_role, "\
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


class TestStackSceptreUserData(object):
    def test_user_data_is_accessible(self):
        """
        .sceptre_user_data is a property. Let's make sure it accesses the right
        data.
        """
        stack = stack_factory(sceptre_user_data={'test_key': sentinel.test_value})
        assert stack.sceptre_user_data['test_key'] is sentinel.test_value

    def test_user_data_gets_resolved(self):
        class TestResolver(Resolver):
            def setup(self):
                pass

            def resolve(self):
                return sentinel.resolved_value

        stack = stack_factory(sceptre_user_data={'test_key': TestResolver()})
        assert stack.sceptre_user_data['test_key'] is sentinel.resolved_value

    def test_recursive_user_data_gets_resolved(self):
        """
        .sceptre_user_data can have resolvers that refer to .sceptre_user_data itself.
        Those must be instantiated before the attribute can be used.
        """
        class TestResolver(Resolver):
            def setup(self):
                pass

            def resolve(self):
                return self.stack.sceptre_user_data['primitive']

        stack = stack_factory()
        stack._sceptre_user_data = {
            'primitive': sentinel.primitive_value,
            'resolved': TestResolver(stack=stack),
        }
        assert stack.sceptre_user_data['resolved'] == sentinel.primitive_value
