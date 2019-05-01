# -*- coding: utf-8 -*-

"""
sceptre.template

This module implements a Template class, which stores a CloudFormation template
and implements methods for uploading it to S3.
"""

import imp
import logging
import os
import sys
import threading

import botocore
import jinja2
from .exceptions import UnsupportedTemplateFileTypeError
from .exceptions import TemplateSceptreHandlerError


class Template(object):
    """
    Template represents an AWS CloudFormation template. It is responsible for
    loading, storing and optionally uploading local templates for use by
    CloudFormation.

    :param path: The absolute path to the file which stores the CloudFormation\
            template.
    :type path: str

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
        self, path, sceptre_user_data, connection_manager=None, s3_details=None
    ):
        self.logger = logging.getLogger(__name__)

        self.path = path
        self.sceptre_user_data = sceptre_user_data
        self.connection_manager = connection_manager
        self.s3_details = s3_details

        self.name = os.path.basename(path).split(".")[0]
        self._body = None

    def __repr__(self):
        return (
            "sceptre.template.Template(name='{0}', path='{1}', "
            "sceptre_user_data={2}, s3_details={3})".format(
                self.name, self.path, self.sceptre_user_data, self.s3_details
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
            file_extension = os.path.splitext(self.path)[1]

            if file_extension in {".json", ".yaml", ".template"}:
                with open(self.path) as template_file:
                    self._body = template_file.read()
            elif file_extension == ".j2":
                self._body = self._render_jinja_template(
                    os.path.dirname(self.path),
                    os.path.basename(self.path),
                    {"sceptre_user_data": self.sceptre_user_data}
                )
            elif file_extension == ".py":
                self._body = self._call_sceptre_handler()

            else:
                raise UnsupportedTemplateFileTypeError(
                    "Template has file extension %s. Only .py, .yaml, "
                    ".template, .json and .j2 are supported.",
                    os.path.splitext(self.path)[1]
                )
        return self._body

    def _call_sceptre_handler(self):
        """
        Calls the function `sceptre_handler` within templates that are python
        scripts.

        :returns: The string returned from sceptre_handler in the template.
        :rtype: str
        :raises: IOError
        :raises: TemplateSceptreHandlerError
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
        self.logger.debug(
            "%s - Getting CloudFormation from %s", self.name, self.path
        )

        if not os.path.isfile(self.path):
            raise IOError("No such file or directory: '%s'", self.path)

        module = imp.load_source(self.name, self.path)

        try:
            body = module.sceptre_handler(self.sceptre_user_data)
        except AttributeError as e:
            if 'sceptre_handler' in str(e):
                raise TemplateSceptreHandlerError(
                    "The template does not have the required "
                    "'sceptre_handler(sceptre_user_data)' function."
                )
            else:
                raise e
        for directory in relpaths_to_add:
            sys.path.remove(os.path.join(os.getcwd(), directory))
        return body

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

    @staticmethod
    def _render_jinja_template(template_dir, filename, jinja_vars):
        """
        Renders a jinja template.

        Sceptre supports passing sceptre_user_data to JSON and YAML
        CloudFormation templates using Jinja2 templating.

        :param template_dir: The directory containing the template.
        :type template_dir: str
        :param filename: The name of the template file.
        :type filename: str
        :param jinja_vars: Dict of variables to render into the template.
        :type jinja_vars: dict
        :returns: The body of the CloudFormation template.
        :rtype: str
        """
        logger = logging.getLogger(__name__)
        logger.debug("%s Rendering CloudFormation template", filename)
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            undefined=jinja2.StrictUndefined
        )
        template = env.get_template(filename)
        body = template.render(**jinja_vars)
        return body
