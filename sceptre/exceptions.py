# -*- coding: utf-8 -*-


class SceptreException(Exception):
    """
    Base class for all Sceptre errors
    """


class ProjectAlreadyExistsError(SceptreException):
    """
    Error raised when Sceptre project already exists.
    """
    pass


class EnvironmentPathNotFoundError(SceptreException):
    """
    Error raised if a directory does not exist
    """
    pass


class NonLeafEnvironmentError(SceptreException):
    """
    Error raised if a directory does not exist
    """
    pass


class InvalidEnvironmentPathError(SceptreException):
    """
    Error raised if the environment path string is invalid
    """
    pass


class ConfigItemNotFoundError(SceptreException):
    """
    Error raised if a necessary config item has not been provided
    """
    pass


class UnsupportedTemplateFileTypeError(SceptreException):
    """
    Error raised if an unsupported template file type is used.
    """
    pass


class TemplateSceptreHandlerError(SceptreException):
    """
    Error raised if sceptre_handler() is not defined correctly in the template.
    """
    pass


class DependencyStackNotLaunchedError(SceptreException):
    """
    Error raised when a dependency stack has not been launched
    """
    pass


class DependencyStackMissingOutputError(SceptreException):
    """
    Error raised if a dependency stack does not have the correct outputs.
    """
    pass


class CircularDependenciesError(SceptreException):
    """
    Error raised if there are circular dependencies
    """
    pass


class UnknownStackStatusError(SceptreException):
    """
    Error raised if an unknown stack status is received.
    """
    pass


class RetryLimitExceededError(SceptreException):
    """
    Error raised if the request limit is exceeded.
    """
    pass


class UnknownHookTypeError(SceptreException):
    """
    Error raised if an unrecognised hook type is received.
    """


class VersionIncompatibleError(SceptreException):
    """
    Error raised if configuration incompatible with running version.
    """
    pass


class ProtectedStackError(SceptreException):
    """
    Error raised upon execution of an action under active protection
    """
    pass


class UnknownStackChangeSetStatusError(SceptreException):
    """
    Error raised if an unknown stack change set status is received.
    """
    pass


class InvalidHookArgumentTypeError(SceptreException):
    """
    Error raised if a hook's argument type is invalid.
    """


class InvalidHookArgumentSyntaxError(SceptreException):
    """
    Error raised if a hook's argument syntax is invalid.
    """


class InvalidHookArgumentValueError(SceptreException):
    """
    Error raised if a hook's argument value is invalid.
    """


class CannotUpdateFailedStackError(SceptreException):
    """
    Error raised when a failed stack is updated.
    """


class StackDoesNotExistError(SceptreException):
    """
    Error raised when a stack does not exist.
    """
    pass


class StackConfigurationDoesNotExistError(SceptreException):
    """
    Error raised when a stack configuration does not exist.
    """
    def __init__(self, error_message):
        self.error_message = error_message


class BotoSessionNotConfiguredError(SceptreException):
    """
    Error raised when ConnectionManager can't create a session.
    """
    pass


class StackDoesNotHaveOutputsError(SceptreException):
    """
    Error raised when Stack Outputs do not exist can't create a session.
    """
    pass
