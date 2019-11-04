# -*- coding: utf-8 -*-
import abc
import logging

import six
from jsonschema import validate, ValidationError

from sceptre.exceptions import TemplateHandlerArgumentsInvalidError


@six.add_metaclass(abc.ABCMeta)
class TemplateHandler:
    """
    TemplateHandler is an abstract base class that should be inherited
    by all Template Handlers.

    :param name: Name of the template
    :type name: str

    :param arguments: The arguments of the template handler
    :type arguments: dict

    :param sceptre_user_data: Sceptre user data in stack config
    :type sceptre_user_data: dict

    :param connection_manager: Connection manager used to call AWS
    :type connection_manager: sceptre.connection_manager.ConnectionManager
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, name, arguments=None, sceptre_user_data=None, connection_manager=None):
        self.logger = logging.getLogger(__name__)
        self.name = name
        self.arguments = arguments
        self.sceptre_user_data = sceptre_user_data
        self.connection_manager = connection_manager

    @abc.abstractmethod
    def schema(self):
        """
        Returns the schema for the arguments of this Template Resolver. This will
        be used to validate that the arguments passed in the stack config are what
        the Template Handler expects.
        :return: JSON schema that can be validated
        :rtype: object
        """
        pass

    @abc.abstractmethod
    def handle(self):
        """
        An abstract method which must be overwritten by all inheriting classes.
        This method is called to retrieve the template.
        Implementation of this method in subclasses must return a string that
        can be interpreted by Sceptre (CloudFormation YAML / JSON, Jinja or Python)
        """
        pass  # pragma: no cover

    def validate(self):
        """
        Validates if the current arguments are correct according to the schema. If this
        does not raise an exception, the template handler's arguments are valid.
        """
        try:
            validate(instance=self.arguments, schema=self.schema())
        except ValidationError as e:
            raise TemplateHandlerArgumentsInvalidError(e)
