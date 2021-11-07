import typing
from contextlib import contextmanager
from enum import Enum

if typing.TYPE_CHECKING:
    from sceptre import resolvers

# This is a toggle used for globally enabling placeholder values out of resolvers when they error
# while resolving. This is important when performing actions on stacks like validation or generation
# when their dependencies have not been deployed yet and those dependencies are expressed in stack
# resolvers that are used in those actions, especially sceptre_user_data.
RESOLVE_PLACEHOLDER_ON_ERROR = False


class PlaceholderType(Enum):
    explicit = 1
    alphanum = 2


_PLACEHOLDER_TYPE = PlaceholderType.explicit


@contextmanager
def use_resolver_placeholders_on_error(placeholder_type: PlaceholderType = PlaceholderType.explicit):
    """A context manager that toggles on placeholders for resolvers that error out. This should NOT
    be used while creating/launching stacks, but it is often required when validating or generating
    stacks whose dependencies haven't yet been deployed and that reference those dependencies with
    resolvers, especially in the sceptre_user_data.

    :param placeholder_type: The type of placeholder that should be resolved when resolvers encounter
        an error. The "explicit" enum will
    """
    global RESOLVE_PLACEHOLDER_ON_ERROR
    global _PLACEHOLDER_TYPE
    try:
        RESOLVE_PLACEHOLDER_ON_ERROR = True
        _PLACEHOLDER_TYPE = placeholder_type
        yield
    finally:
        RESOLVE_PLACEHOLDER_ON_ERROR = False


def create_placeholder_value(resolver: 'resolvers.Resolver'):
    placeholder_func = _placeholders[_PLACEHOLDER_TYPE]
    return placeholder_func(resolver)


def _create_explicit_resolver_placeholder(resolver: 'resolvers.Resolver') -> str:
    """Creates a placeholder value to be substituted for the resolved value when placeholders are
    allowed and the value cannot be resolved.

    The placeholder will look like one of:
      * { !ClassName } -> used when there is no argument
      * { !ClassName(argument) } -> used when there is a string argument
      * { !ClassName({'key': 'value'}) } -> used when there is a dict argument

    :param resolver: The resolver to create a placeholder for
    :return: The placeholder value
    """
    base = f'!{type(resolver).__name__}'
    suffix = f'({resolver.argument})' if resolver.argument is not None else ''
    # double-braces in an f-string is just an escaped single brace
    return f'{{ {base}{suffix} }}'


def _create_alphanumeric_placeholder(resolver: 'resolvers.Resolver') -> str:
    """Creates a placeholder value that is only composed of alphanumeric characters. This is more
    useful when performing operations that send a template to CloudFormation, which will have stricter
    requirements for values in templates.

    Values from this function will not be as readable, but they are more likely to be valid when passed
    to a template.

    The placeholder will look like one of:
    * ClassName -> used when there is no argument
    * ClassNameargument -> used when there is a string argument
    * ClassNamekeyvalue -> used when there is a dict argument

    :param resolver: The resolver to create a placeholder for
    :return: The placeholder value
    """
    explicit_placeholder = _create_explicit_resolver_placeholder(resolver)
    alphanum_placeholder = ''.join(c for c in explicit_placeholder if c.isalnum())
    return alphanum_placeholder


_placeholders = {
    PlaceholderType.explicit: _create_explicit_resolver_placeholder,
    PlaceholderType.alphanum: _create_alphanumeric_placeholder
}
