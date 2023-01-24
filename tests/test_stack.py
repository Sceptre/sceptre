# -*- coding: utf-8 -*-

from unittest.mock import MagicMock, sentinel

import deprecation
import pytest

from sceptre.exceptions import InvalidConfigFileError
from sceptre.resolvers import Resolver
from sceptre.stack import Stack
from sceptre.template import Template


def stack_factory(**kwargs):
    call_kwargs = {
        "name": "dev/app/stack",
        "project_code": sentinel.project_code,
        "template_bucket_name": sentinel.template_bucket_name,
        "template_key_prefix": sentinel.template_key_prefix,
        "required_version": sentinel.required_version,
        "template_path": sentinel.template_path,
        "region": sentinel.region,
        "profile": sentinel.profile,
        "parameters": {"key1": "val1"},
        "sceptre_user_data": sentinel.sceptre_user_data,
        "hooks": {},
        "s3_details": None,
        "dependencies": sentinel.dependencies,
        "role_arn": sentinel.role_arn,
        "protected": False,
        "tags": {"tag1": "val1"},
        "external_name": sentinel.external_name,
        "notifications": [sentinel.notification],
        "on_failure": sentinel.on_failure,
        "disable_rollback": False,
        "stack_timeout": sentinel.stack_timeout,
        "stack_group_config": {},
    }
    call_kwargs.update(kwargs)
    return Stack(**call_kwargs)


class TestStack(object):
    def setup_method(self, test_method):
        self.stack = Stack(
            name="dev/app/stack",
            project_code=sentinel.project_code,
            template_bucket_name=sentinel.template_bucket_name,
            template_key_prefix=sentinel.template_key_prefix,
            required_version=sentinel.required_version,
            template_path=sentinel.template_path,
            region=sentinel.region,
            profile=sentinel.profile,
            parameters={"key1": "val1"},
            sceptre_user_data=sentinel.sceptre_user_data,
            hooks={},
            s3_details=None,
            dependencies=sentinel.dependencies,
            role_arn=sentinel.role_arn,
            protected=False,
            tags={"tag1": "val1"},
            external_name=sentinel.external_name,
            notifications=[sentinel.notification],
            on_failure=sentinel.on_failure,
            disable_rollback=False,
            sceptre_role=sentinel.sceptre_role,
            sceptre_role_session_duration=sentinel.sceptre_role_session_duration,
            stack_timeout=sentinel.stack_timeout,
            stack_group_config={},
        )
        self.stack._template = MagicMock(spec=Template)

    def test_initialize_stack_with_template_path(self):
        stack = Stack(
            name="dev/stack/app",
            project_code=sentinel.project_code,
            template_path=sentinel.template_path,
            template_bucket_name=sentinel.template_bucket_name,
            template_key_prefix=sentinel.template_key_prefix,
            required_version=sentinel.required_version,
            region=sentinel.region,
            external_name=sentinel.external_name,
        )
        assert stack.name == "dev/stack/app"
        assert stack.project_code == sentinel.project_code
        assert stack.template_bucket_name == sentinel.template_bucket_name
        assert stack.template_key_prefix == sentinel.template_key_prefix
        assert stack.required_version == sentinel.required_version
        assert stack.external_name == sentinel.external_name
        assert stack.hooks == {}
        assert stack.parameters == {}
        assert stack.sceptre_user_data == {}
        assert stack.template_path == sentinel.template_path
        assert stack.template_handler_config == {
            "path": sentinel.template_path,
            "type": "file",
        }
        assert stack.s3_details is None
        assert stack._template is None
        assert stack.protected is False
        assert stack.sceptre_role is None
        assert stack.role_arn is None
        assert stack.dependencies == []
        assert stack.tags == {}
        assert stack.notifications == []
        assert stack.on_failure is None
        assert stack.disable_rollback is False
        assert stack.stack_group_config == {}

    def test_initialize_stack_with_template_handler(self):
        expected_template_handler_config = {
            "type": "file",
            "path": sentinel.template_path,
        }
        stack = Stack(
            name="dev/stack/app",
            project_code=sentinel.project_code,
            template_handler_config=expected_template_handler_config,
            template_bucket_name=sentinel.template_bucket_name,
            template_key_prefix=sentinel.template_key_prefix,
            required_version=sentinel.required_version,
            region=sentinel.region,
            external_name=sentinel.external_name,
        )
        assert stack.name == "dev/stack/app"
        assert stack.project_code == sentinel.project_code
        assert stack.template_bucket_name == sentinel.template_bucket_name
        assert stack.template_key_prefix == sentinel.template_key_prefix
        assert stack.required_version == sentinel.required_version
        assert stack.external_name == sentinel.external_name
        assert stack.hooks == {}
        assert stack.parameters == {}
        assert stack.sceptre_user_data == {}
        assert stack.template_path == sentinel.template_path
        assert stack.template_handler_config == expected_template_handler_config
        assert stack.s3_details is None
        assert stack._template is None
        assert stack.protected is False
        assert stack.sceptre_role is None
        assert stack.role_arn is None
        assert stack.dependencies == []
        assert stack.tags == {}
        assert stack.notifications == []
        assert stack.on_failure is None
        assert stack.disable_rollback is False
        assert stack.stack_group_config == {}

    def test_raises_exception_if_path_and_handler_configured(self):
        with pytest.raises(InvalidConfigFileError):
            Stack(
                name="stack_name",
                project_code="project_code",
                template_path="template_path",
                template_handler_config={"type": "file"},
                region="region",
            )

    def test_init__non_boolean_ignore_value__raises_invalid_config_file_error(self):
        with pytest.raises(InvalidConfigFileError):
            Stack(
                name="dev/stack/app",
                project_code=sentinel.project_code,
                template_handler_config=sentinel.template_handler_config,
                template_bucket_name=sentinel.template_bucket_name,
                template_key_prefix=sentinel.template_key_prefix,
                required_version=sentinel.required_version,
                region=sentinel.region,
                external_name=sentinel.external_name,
                ignore="true",
            )

    def test_init__non_boolean_obsolete_value__raises_invalid_config_file_error(self):
        with pytest.raises(InvalidConfigFileError):
            Stack(
                name="dev/stack/app",
                project_code=sentinel.project_code,
                template_handler_config=sentinel.template_handler_config,
                template_bucket_name=sentinel.template_bucket_name,
                template_key_prefix=sentinel.template_key_prefix,
                required_version=sentinel.required_version,
                region=sentinel.region,
                external_name=sentinel.external_name,
                obsolete="true",
            )

    def test_stack_repr(self):
        assert (
            self.stack.__repr__() == "sceptre.stack.Stack("
            "name='dev/app/stack', "
            "project_code=sentinel.project_code, "
            "template_handler_config={'type': 'file', 'path': sentinel.template_path}, "
            "region=sentinel.region, "
            "template_bucket_name=sentinel.template_bucket_name, "
            "template_key_prefix=sentinel.template_key_prefix, "
            "required_version=sentinel.required_version, "
            "sceptre_role=sentinel.sceptre_role, "
            "sceptre_role_session_duration=sentinel.sceptre_role_session_duration, "
            "profile=sentinel.profile, "
            "sceptre_user_data=sentinel.sceptre_user_data, "
            "parameters={'key1': 'val1'}, "
            "hooks={}, "
            "s3_details=None, "
            "dependencies=sentinel.dependencies, "
            "cloudformation_service_role=sentinel.role_arn, "
            "protected=False, "
            "tags={'tag1': 'val1'}, "
            "external_name=sentinel.external_name, "
            "notifications=[sentinel.notification], "
            "on_failure=sentinel.on_failure, "
            "disable_rollback=False, "
            "stack_timeout=sentinel.stack_timeout, "
            "stack_group_config={}, "
            "ignore=False, "
            "obsolete=False"
            ")"
        )

    def test_configuration_manager__sceptre_role_raises_recursive_resolve__returns_connection_manager_with_no_role(
        self,
    ):
        class FakeResolver(Resolver):
            def resolve(self):
                return self.stack.sceptre_role

        self.stack.sceptre_role = FakeResolver()

        connection_manager = self.stack.connection_manager
        assert connection_manager.sceptre_role is None

    def test_configuration_manager__sceptre_role_returns_value_second_access__returns_value_on_second_access(
        self,
    ):
        class FakeResolver(Resolver):
            access_count = 0

            def resolve(self):
                if self.access_count == 0:
                    self.access_count += 1
                    return self.stack.sceptre_role
                else:
                    return "role"

        self.stack.sceptre_role = FakeResolver()

        assert self.stack.connection_manager.sceptre_role is None
        assert self.stack.connection_manager.sceptre_role == "role"

    def test_configuration_manager__sceptre_role_returns_value__returns_connection_manager_with_that_role(
        self,
    ):
        class FakeResolver(Resolver):
            def resolve(self):
                return "role"

        self.stack.sceptre_role = FakeResolver()

        connection_manager = self.stack.connection_manager
        assert connection_manager.sceptre_role == "role"

    @deprecation.fail_if_not_removed
    def test_iam_role__is_removed_on_removal_version(self):
        self.stack.iam_role

    @deprecation.fail_if_not_removed
    def test_role_arn__is_removed_on_removal_version(self):
        self.stack.role_arn

    @deprecation.fail_if_not_removed
    def test_iam_role_session_duration__is_removed_on_removal_version(self):
        self.stack.iam_role_session_duration

    def test_init__iam_role_set_resolves_to_sceptre_role(self):
        stack = Stack("test", "test", "test", "test", iam_role="fancy")
        assert stack.sceptre_role == "fancy"

    def test_init__role_arn_set_resolves_to_cloudformation_service_role(self):
        stack = Stack("test", "test", "test", "test", role_arn="fancy")
        assert stack.cloudformation_service_role == "fancy"

    def test_init__iam_role_session_duration_set_resolves_to_sceptre_role_session_duration(
        self,
    ):
        stack = Stack("test", "test", "test", "test", iam_role_session_duration=123456)
        assert stack.sceptre_role_session_duration == 123456


class TestStackSceptreUserData(object):
    def test_user_data_is_accessible(self):
        """
        .sceptre_user_data is a property. Let's make sure it accesses the right
        data.
        """
        stack = stack_factory(sceptre_user_data={"test_key": sentinel.test_value})
        assert stack.sceptre_user_data["test_key"] is sentinel.test_value

    def test_user_data_gets_resolved(self):
        class TestResolver(Resolver):
            def setup(self):
                pass

            def resolve(self):
                return sentinel.resolved_value

        stack = stack_factory(sceptre_user_data={"test_key": TestResolver()})
        assert stack.sceptre_user_data["test_key"] is sentinel.resolved_value

    def test_recursive_user_data_gets_resolved(self):
        """
        .sceptre_user_data can have resolvers that refer to .sceptre_user_data itself.
        Those must be instantiated before the attribute can be used.
        """

        class TestResolver(Resolver):
            def setup(self):
                pass

            def resolve(self):
                return self.stack.sceptre_user_data["primitive"]

        stack = stack_factory()
        stack.sceptre_user_data = {
            "primitive": sentinel.primitive_value,
            "resolved": TestResolver(stack=stack),
        }
        assert stack.sceptre_user_data["resolved"] == sentinel.primitive_value
