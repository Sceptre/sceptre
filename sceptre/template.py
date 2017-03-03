# -*- coding: utf-8 -*-

"""
sceptre.template

This module implements a Template class, which stores a CloudFormation template
and implements methods for uploading it to S3.
"""

from datetime import datetime
import imp
import logging
import os
import sys
import threading

import botocore

from .exceptions import UnsupportedTemplateFileTypeError
from .exceptions import TemplateSceptreHandlerError


class Template(object):
    """
    Template represents an AWS CloudFormation template. It is responsible for
    loading, storing, and optionally uploading, local templates for use by the
    CloudFormation service.

    :param path: The absolute path to the file which stores the template.
    :type path: str
    :param sceptre_user_data: A dictionary of arbitrary data to be passed to \
        a handler function in an external Python script.
    :type sceptre_user_data: dict
    """

    _create_bucket_lock = threading.Lock()

    def __init__(self, path, sceptre_user_data):
        self.logger = logging.getLogger(__name__)

        self.path = path
        self.sceptre_user_data = sceptre_user_data
        self.name = os.path.basename(path).split(".")[0]
        self._body = None

    def __repr__(self):
        return (
            "sceptre.template.Template(name='{0}', path='{1}', "
            "sceptre_user_data={2})".format(
                self.name, self.path, self.sceptre_user_data
            )
        )

    @property
    def body(self):
        """
        Returns the CloudFormation template.

        :returns: The CloudFormation template.
        :rtype: str
        """
        if self._body is None:
            self._body = self._get_body()
        return self._body

    def upload_to_s3(
            self, region, bucket_name, key_prefix, environment_path,
            stack_name, connection_manager
    ):
        """
        Uploads the template to ``bucket_name`` and returns its URL.

        The template is uploaded with the key
        ``<key_prefix>/<region>/<environment_path>/<stack_name>-<timestamp>.json``.

        :param region: The AWS region to create the bucket in.
        :type region: str
        :param bucket_name: The name of the bucket to create.
        :type bucket_name: str
        :param key_prefix: A string to prefix to the key used to store the
            template in S3.
        :type key_prefix: str
        :param environment_path: The environment that the stack belongs to.
        :type env_path: str
        :param stack_name: The name of the stack that this template creates.
        :type stack_name: str
        :param connection_manager: The connection manager used to make
            AWS calls.
        :type connection_manager: sceptre.connection_manager.ConnectionManager
        :returns: The URL of the template object in S3.
        :rtype: str
        :raises: botocore.exceptions.ClientError

        """
        self.logger.debug("%s - Uploading template to S3...", self.name)

        self._create_bucket(region, bucket_name, connection_manager)

        # Remove any leading or trailing slashes the user may have added.
        key_prefix = key_prefix.strip("/")

        template_key = "/".join([
            key_prefix,
            region,
            environment_path,
            "{stack_name}-{time_stamp}.json".format(
                stack_name=stack_name,
                time_stamp=datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%fZ")
            )
        ])

        self.logger.debug(
            "%s - Uploading template to: 's3://%s/%s'",
            self.name, bucket_name, template_key
        )
        connection_manager.call(
            service="s3",
            command="put_object",
            kwargs={
                "Bucket": bucket_name,
                "Key": template_key,
                "Body": self.body,
                "ServerSideEncryption": "AES256"
            }
        )

        url = "https://{0}.s3.amazonaws.com/{1}".format(
            bucket_name, template_key
        )

        self.logger.debug("%s - Template URL: '%s'", self.name, url)

        return url

    def _create_bucket(
            self, region, bucket_name, connection_manager
    ):
        """
        Create the bucket ``bucket_name`` in the region ``region``.

        This is done in a thread-safe way. No error is raised if the bucket
        already exists.

        :param region: The AWS region to create the bucket in.
        :type region: str
        :param bucket_name: The name of the bucket to create.
        :type bucket_name: str
        :param connection_manager: The connection manager used to make
            AWS calls.
        :type connection_manager: sceptre.connection_manager.ConnectionManager
        :raises: botocore.exception.ClientError

        """
        with self._create_bucket_lock:
            try:
                self.logger.debug(
                    "%s - Attempting to find template bucket '%s'",
                    self.name, bucket_name
                )
                connection_manager.call(
                    service="s3",
                    command="head_bucket",
                    kwargs={"Bucket": bucket_name}
                )
                self.logger.debug(
                    "%s - Found template bucket '%s'", self.name, bucket_name
                )
            except botocore.exceptions.ClientError as exp:
                if exp.response["Error"]["Message"] == "Not Found":
                    self.logger.debug(
                        "%s - No bucket found. Creating new template "
                        "bucket '%s'", self.name, bucket_name
                    )
                    if region == "us-east-1":
                        connection_manager.call(
                            service="s3",
                            command="create_bucket",
                            kwargs={"Bucket": bucket_name}
                        )
                    else:
                        connection_manager.call(
                            service="s3",
                            command="create_bucket",
                            kwargs={
                                "Bucket": bucket_name,
                                "CreateBucketConfiguration": {
                                    "LocationConstraint": region
                                }
                            }
                        )
                else:
                    raise

    def _get_body(self):
        """
        Reads in a CloudFormation template directly from a file or as a string
        from an external Python script (such as Troposphere).

        External Python scripts have arbitrary dictionary of data
        (sceptre_user_data) passed to them.

        :returns: A CloudFormation template
        :rtype: str
        :raises: sceptre.stack.UnsupportedTemplateFileTypeException
        :raises: IOError
        """
        # Get relative path as list between current working directory and where
        # the template is
        # NB: this is a horrible hack...
        relpath = os.path.relpath(self.path, os.getcwd()).split(os.path.sep)
        relpaths_to_add = [
            os.path.sep.join(relpath[:i+1])
            for i in range(len(relpath[:-1]))
        ]

        # Add any directory between the current working directory and where
        # the template is to the python path
        for directory in relpaths_to_add:
            sys.path.append(os.path.join(os.getcwd(), directory))

        self.file_extension = os.path.splitext(self.path)[1]

        if self.file_extension in (".json", ".yaml"):
            self.logger.debug("%s - Opening file %s", self.name, self.path)
            with open(self.path) as template_file:
                body = template_file.read()
        elif self.file_extension == ".py":
            self.logger.debug(
                "%s - Getting CloudFormation from %s", self.name, self.path
            )

            # If imp.load_source cannot find the file at self.path, it throws
            # an IOError, but doesn't specify which file couldn't be found.
            # As multiple templates are loaded when an environment is built,
            # more detail is needed. The following commmand
            # "looks before we leap", and specifies which file can't be found.
            if not os.path.isfile(self.path):
                raise IOError("No such file or directory: '%s'", self.path)

            module = imp.load_source(self.name, self.path)

            if hasattr(module, "sceptre_handler"):
                    body = module.sceptre_handler(self.sceptre_user_data)
            else:
                raise TemplateSceptreHandlerError(
                    "The template does not have the required "
                    "'sceptre_handler(sceptre_user_data)' function."
                )
        else:
            raise UnsupportedTemplateFileTypeError(
                "Template has file extension `{0}`. Only .py, .yaml, and "
                ".json are supported.".format(os.path.splitext(self.path)[1])
            )

        for directory in relpaths_to_add:
            sys.path.remove(os.path.join(os.getcwd(), directory))

        return body
