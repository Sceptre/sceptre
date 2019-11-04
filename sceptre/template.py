# -*- coding: utf-8 -*-

"""
sceptre.template

This module implements a Template class, which stores a CloudFormation template
and implements methods for uploading it to S3.
"""

import logging
import os
import sys
import threading
import traceback

import botocore
from pkg_resources import iter_entry_points

from sceptre.exceptions import TemplateHandlerNotFoundError


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

    :param connection_manager:
    :type connection_manager: sceptre.connection_manager.ConnectionManager

    :param s3_details:
    :type s3_details: dict
    """

    _boto_s3_lock = threading.Lock()

    def __init__(
            self, name, handler_config, sceptre_user_data, connection_manager=None, s3_details=None
    ):
        self.logger = logging.getLogger(__name__)

        self.name = name
        self.handler_config = handler_config
        self.sceptre_user_data = sceptre_user_data
        self.connection_manager = connection_manager
        self.s3_details = s3_details

        self._registry = None
        self._body = None

    def __repr__(self):
        return (
            "sceptre.template.Template(name='{0}', handler_config={1}, sceptre_user_data={2}, s3_details={3})".format(
                self.name, self.handler_config, self.sceptre_user_data, self.s3_details
            )
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
                connection_manager=self.connection_manager
            )
            handler.validate()
            body = handler.handle()
            if isinstance(body, bytes):
                body = body.decode('utf-8')
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
        bucket_region = self.s3_details["bucket_region"]

        self.logger.debug(
            "%s - Uploading template to: 's3://%s/%s'",
            self.name, bucket_name, bucket_key
        )
        self.connection_manager.call(
            service="s3",
            command="put_object",
            kwargs={
                "Bucket": bucket_name,
                "Key": bucket_key,
                "Body": self.body,
                "ServerSideEncryption": "AES256"
            }
        )

        china_regions = ["cn-north-1", "cn-northwest-1"]

        if bucket_region in china_regions:
            url = "https://{0}.s3.{1}.amazonaws.com.cn/{2}".format(
                bucket_name, bucket_region, bucket_key
            )
        else:
            url = "https://{0}.s3.amazonaws.com/{1}".format(
                bucket_name, bucket_key
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
            "%s - Attempting to find template bucket '%s'",
            self.name, bucket_name
        )
        try:
            self.connection_manager.call(
                service="s3",
                command="head_bucket",
                kwargs={"Bucket": bucket_name}
            )
        except botocore.exceptions.ClientError as exp:
            if exp.response["Error"]["Message"] == "Not Found":
                self.logger.debug(
                    "%s - %s bucket not found.", self.name, bucket_name
                )
                return False
            else:
                raise
        self.logger.debug(
            "%s - Found template bucket '%s'", self.name, bucket_name
        )
        return True

    def _create_bucket(self):
        """
        Create the s3 bucket ``bucket_name``.

        :raises: botocore.exception.ClientError

        """
        bucket_name = self.s3_details["bucket_name"]

        self.logger.debug(
            "%s - Creating new bucket '%s'", self.name, bucket_name
        )

        if self.connection_manager.region == "us-east-1":
            self.connection_manager.call(
                service="s3",
                command="create_bucket",
                kwargs={"Bucket": bucket_name}
            )
        else:
            self.connection_manager.call(
                service="s3",
                command="create_bucket",
                kwargs={
                    "Bucket": bucket_name,
                    "CreateBucketConfiguration": {
                        "LocationConstraint": self.connection_manager.region
                    }
                }
            )

    def get_boto_call_parameter(self):
        """
        Returns the CloudFormation template location.

        Uploads the template to S3 and returns the object's URL, or returns
        the template itself.

        :returns: The boto call parameter for the template.
        :rtype: dict
        """
        if self.s3_details:
            url = self.upload_to_s3()
            return {"TemplateURL": url}
        else:
            return {"TemplateBody": self.body}

    def _get_handler_of_type(self, type):
        """
        Gets a TemplateHandler typ from the registry that can be used to get a string
        representation of a CloudFormation template.
        :param type: The type of Template Handler to load
        :type type: str
        :return: Instantiated TemplateHandler
        :rtype: class
        """
        if not self._registry:
            self._registry = {}

            for entry_point in iter_entry_points("sceptre.template_handlers", type):
                self._registry[entry_point.name] = entry_point.load()

        if type not in self._registry:
            raise TemplateHandlerNotFoundError('Handler of type "{0}" not found'.format(type))

        return self._registry[type]
