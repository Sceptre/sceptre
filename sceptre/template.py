# -*- coding: utf-8 -*-

"""
sceptre.template

This module implements a Template class, which stores a CloudFormation template
and implements methods for uploading it to S3.
"""

import logging
import threading
import botocore
import sys

import sceptre.helpers

from sceptre.exceptions import TemplateHandlerNotFoundError
from sceptre.logging import StackLoggerAdapter


class Template(object):
    """
    Template represents an AWS CloudFormation template. It is responsible for
    loading, storing and optionally uploading local templates for use by
    CloudFormation.

    :param name: The name of the template. Should be safe to use in filenames and not contain path segments.
    :type name: str

    :param handler_config: The configuration for a Template handler. Must contain a `type`.
    :type handler_config: dict

    :param sceptre_user_data: A dictionary of arbitrary data to be passed to\
            a handler function in an external Python script.
    :type sceptre_user_data: dict

    :param stack_group_config: The StackGroup config for the Stack.
    :type stack_group_config: dict

    :param connection_manager:
    :type connection_manager: sceptre.connection_manager.ConnectionManager

    :param s3_details:
    :type s3_details: dict
    """

    _boto_s3_lock = threading.Lock()

    def __init__(
        self,
        name,
        handler_config,
        sceptre_user_data,
        stack_group_config,
        connection_manager=None,
        s3_details=None,
    ):
        self.logger = StackLoggerAdapter(logging.getLogger(__name__), name)
        self.name = name
        self.handler_config = handler_config
        if self.handler_config is not None and self.handler_config.get("type") is None:
            self.handler_config["type"] = "file"
        self.sceptre_user_data = sceptre_user_data
        self.stack_group_config = stack_group_config
        self.connection_manager = connection_manager
        self.s3_details = s3_details

        self._registry = None
        self._body = None

    def __repr__(self):
        return sceptre.helpers.gen_repr(
            self,
            class_label="sceptre.template.Template",
            attributes=["name", "handler_config", "sceptre_user_data", "s3_details"],
        )

    @property
    def body(self):
        """
        Represents body of the CloudFormation template.

        :returns: The body of the CloudFormation template.
        :rtype: str
        """
        if self._body is None:
            type = self.handler_config.get("type")
            handler_class = self._get_handler_of_type(type)
            handler = handler_class(
                name=self.name,
                arguments={k: v for k, v in self.handler_config.items() if k != "type"},
                sceptre_user_data=self.sceptre_user_data,
                connection_manager=self.connection_manager,
                stack_group_config=self.stack_group_config,
            )
            handler.validate()
            body = handler.handle()
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            if not str(body).startswith("---"):
                body = "---\n{}".format(body)
            self._body = body

        return self._body

    def upload_to_s3(self):
        """
        Uploads the template to ``bucket_name`` and returns its URL.

        The Template is uploaded with the ``bucket_key``.

        :returns: The URL of the Template object in S3.
        :rtype: str
        :raises: botocore.exceptions.ClientError

        """
        self.logger.debug("%s - Uploading template to S3...", self.name)

        with self._boto_s3_lock:
            if not self._bucket_exists():
                self._create_bucket()

        # Remove any leading or trailing slashes the user may have added.
        bucket_name = self.s3_details["bucket_name"]
        bucket_key = self.s3_details["bucket_key"]
        bucket_region = self._bucket_region(bucket_name)

        self.logger.debug(
            "%s - Uploading template to: 's3://%s/%s'",
            self.name,
            bucket_name,
            bucket_key,
        )
        self.connection_manager.call(
            service="s3",
            command="put_object",
            kwargs={
                "Bucket": bucket_name,
                "Key": bucket_key,
                "Body": self.body,
                "ServerSideEncryption": "AES256",
            },
        )

        url = "https://{}.s3.{}.amazonaws.{}/{}".format(
            bucket_name,
            bucket_region,
            self._domain_from_region(bucket_region),
            bucket_key,
        )

        self.logger.debug("%s - Template URL: '%s'", self.name, url)

        return url

    def _bucket_exists(self):
        """
        Checks if the bucket ``bucket_name`` exists.

        :returns: Boolean whether the bucket exists
        :rtype: bool
        :raises: botocore.exception.ClientError

        """
        bucket_name = self.s3_details["bucket_name"]
        self.logger.debug(
            "%s - Attempting to find template bucket '%s'", self.name, bucket_name
        )
        try:
            self.connection_manager.call(
                service="s3", command="head_bucket", kwargs={"Bucket": bucket_name}
            )
        except botocore.exceptions.ClientError as exp:
            if exp.response["Error"]["Message"] == "Not Found":
                self.logger.debug("%s - %s bucket not found.", self.name, bucket_name)
                return False
            else:
                raise
        self.logger.debug("%s - Found template bucket '%s'", self.name, bucket_name)
        return True

    def _create_bucket(self):
        """
        Create the s3 bucket ``bucket_name``.

        :raises: botocore.exception.ClientError

        """
        bucket_name = self.s3_details["bucket_name"]

        self.logger.debug("%s - Creating new bucket '%s'", self.name, bucket_name)

        if self.connection_manager.region == "us-east-1":
            self.connection_manager.call(
                service="s3", command="create_bucket", kwargs={"Bucket": bucket_name}
            )
        else:
            self.connection_manager.call(
                service="s3",
                command="create_bucket",
                kwargs={
                    "Bucket": bucket_name,
                    "CreateBucketConfiguration": {
                        "LocationConstraint": self.connection_manager.region
                    },
                },
            )

    def get_boto_call_parameter(self):
        """
        Returns the CloudFormation template location.

        Uploads the template to S3 and returns the object's URL, or returns
        the template itself.

        :returns: The boto call parameter for the template.
        :rtype: dict
        """
        # If bucket_name is set to None, it should be ignored and not uploaded.
        if self.s3_details and self.s3_details.get("bucket_name"):
            url = self.upload_to_s3()
            return {"TemplateURL": url}
        else:
            return {"TemplateBody": self.body}

    def _bucket_region(self, bucket_name):
        region = self.connection_manager.call(
            service="s3", command="get_bucket_location", kwargs={"Bucket": bucket_name}
        ).get("LocationConstraint")
        return region if region else "us-east-1"

    @staticmethod
    def _domain_from_region(region):
        return "com.cn" if region.startswith("cn-") else "com"

    @staticmethod
    def _iterate_entry_points(group, name):
        """
        Helper to determine whether to use pkg_resources or importlib.metadata.
        https://docs.python.org/3/library/importlib.metadata.html
        """
        if sys.version_info < (3, 10):
            from pkg_resources import iter_entry_points

            return iter_entry_points(group, name)
        else:
            from importlib.metadata import entry_points

            return entry_points(group=group, name=name)

    def _get_handler_of_type(self, type):
        """
        Gets a TemplateHandler type from the registry that can be used to get a string
        representation of a CloudFormation template.
        :param type: The type of Template Handler to load
        :type type: str
        :return: Instantiated TemplateHandler
        :rtype: class
        """
        if not self._registry:
            self._registry = {}

            for entry_point in self._iterate_entry_points(
                "sceptre.template_handlers", type
            ):
                self._registry[entry_point.name] = entry_point.load()

        if type not in self._registry:
            raise TemplateHandlerNotFoundError(
                'Handler of type "{0}" not found'.format(type)
            )

        return self._registry[type]
