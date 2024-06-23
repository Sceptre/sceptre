# -*- coding: utf-8 -*-
import pathlib
import tempfile
import sceptre.template_handlers.helper as helper

from sceptre.exceptions import UnsupportedTemplateFileTypeError
from sceptre.template_handlers import TemplateHandler


class S3(TemplateHandler):
    """
    Template handler that can resolve templates from S3.  Raw CFN templates
    with extension (.json, .yaml, .template) are deployed directly from memory
    while references to jinja (.j2) and python (.py) templates are downloaded,
    transformed into CFN templates then deployed to AWS.
    """

    def __init__(self, *args, **kwargs):
        super(S3, self).__init__(*args, **kwargs)

    def schema(self):
        return {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        }

    def handle(self):
        """
        handle template in S3 bucket
        """
        input_path = self.arguments["path"]
        path = pathlib.Path(input_path)

        standard_template_suffix = [".json", ".yaml", ".template"]
        jinja_template_suffix = [".j2"]
        python_template_suffix = [".py"]
        supported_suffix = (
            standard_template_suffix + jinja_template_suffix + python_template_suffix
        )

        if path.suffix not in supported_suffix:
            raise UnsupportedTemplateFileTypeError(
                "Template has file extension %s. Only %s are supported.",
                path.suffix,
                ",".join(supported_suffix),
            )

        try:
            template = self._get_template(path)
            if path.suffix in jinja_template_suffix + python_template_suffix:
                file = tempfile.NamedTemporaryFile(prefix=path.stem)
                with file as f:
                    f.write(template)
                    f.seek(0)
                    f.read()
                    if path.suffix in jinja_template_suffix:
                        template = helper.render_jinja_template(
                            f.name,
                            {"sceptre_user_data": self.sceptre_user_data},
                            self.stack_group_config.get("j2_environment", {}),
                        )
                    elif path.suffix in python_template_suffix:
                        template = helper.call_sceptre_handler(
                            f.name, self.sceptre_user_data
                        )

        except Exception as e:
            helper.print_template_traceback(path)
            raise e

        return template

    def _get_template(self, path):
        """
        Get template from S3 bucket

        :param path: The path to the object in the bucket
        :type: str
        :returns: The body of the CloudFormation template.
        :rtype: str
        """
        self.logger.debug("Downloading file from S3: %s", path)
        bucket = path.parts[0]
        key = "/".join(path.parts[1:])

        try:
            response = self.connection_manager.call(
                service="s3",
                command="get_object",
                kwargs={"Bucket": bucket, "Key": key},
            )
            return response["Body"].read()
        except Exception as e:
            self.logger.critical(e)
            raise e
