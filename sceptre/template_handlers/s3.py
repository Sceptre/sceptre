import logging

from sceptre.template_handlers import TemplateHandler


class S3(TemplateHandler):
    """
    Template Handler that can resolve templates from S3.
    """
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        super(S3, self).__init__(*args, **kwargs)

    def schema(self):
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            }
        }

    def handle(self):
        self.logger.debug("Downloading file from S3: %s" % self.argument)

        segments = self.arguments["path"].split('/')
        bucket = segments[0]
        key = "/".join(segments[1:])

        try:
            response = self.connection_manager.call(
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
