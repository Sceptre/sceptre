# -*- coding: utf-8 -*-
import logging

from sceptre.resolvers import Resolver


class S3(Resolver):
    """
    Resolver for the contents of an object in an S3 bucket.

    :param argument: S3 path to object
    :type argument: str
    """

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        super(S3, self).__init__(*args, **kwargs)

    def resolve(self):
        self.logger.debug("Downloading file from S3: %s" % self.argument)

        segments = self.argument.split('/')
        bucket = segments[0]
        key = "/".join(segments[1:])

        connection_manager = self.stack.connection_manager
        try:
            response = connection_manager.call(
                service="s3",
                command="get_object",
                kwargs={
                    "Bucket": bucket,
                    "Key": key
                }
            )
            return response["Body"].read()
        except Exception as e:
            self.logger.fatal(e)
            raise e
