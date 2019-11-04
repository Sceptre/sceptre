# -*- coding: utf-8 -*-
import abc
import logging

import six
from jsonschema import validate


@six.add_metaclass(abc.ABCMeta)
class TemplateHandler:
    """
    TemplateHandler is an abstract base class that should be inherited
    by all Template Handlers.

    :param arguments: The arguments of the template handler
    :type arguments: object
    :param connection_manager: Connection manager used to call AWS
    :type connection_manager: sceptre.connection_manager.ConnectionManager
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, arguments=None, connection_manager=None):
        self.logger = logging.getLogger(__name__)
        self.arguments = arguments
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
        Validates if the current arguments are correct according to the schema.
        :return: True if arguments valid, false if not
        :rtype: bool
        """
        return validate(instance=self.arguments, schema=self.schema())
