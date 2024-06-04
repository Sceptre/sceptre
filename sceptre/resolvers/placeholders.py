from contextlib import contextmanager
from enum import Enum
from threading import Lock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sceptre import resolvers

# This is a toggle used for globally enabling placeholder values out of resolvers when they error
# while resolving. This is important when performing actions on stacks like validation or generation
# when their dependencies have not been deployed yet and those dependencies are expressed in stack
# resolvers that are used in those actions, especially sceptre_user_data.
_RESOLVE_PLACEHOLDER_ON_ERROR = False


class PlaceholderType(Enum):
    explicit = 1  # Looks like "{ !MyClass(argument) }"
    alphanum = 2  # Looks like MyClassargument
    none = 3  # Resolves to None


_placeholder_lock = Lock()


@contextmanager
def use_resolver_placeholders_on_error():
    """A context manager that toggles on placeholders for resolvers that error out. This should NOT
    be used while creating/launching stacks, but it is often required when validating or diffing
    stacks whose dependencies haven't yet been deployed and that reference those dependencies with
    resolvers, especially in the sceptre_user_data.
    """
    global _RESOLVE_PLACEHOLDER_ON_ERROR

    try:
        with _placeholder_lock:
            _RESOLVE_PLACEHOLDER_ON_ERROR = True
        yield
    finally:
        with _placeholder_lock:
            _RESOLVE_PLACEHOLDER_ON_ERROR = False


def are_placeholders_enabled() -> bool:
    """Indicates whether placeholders have been globally enabled or not."""
    with _placeholder_lock:
        return _RESOLVE_PLACEHOLDER_ON_ERROR


def create_placeholder_value(
    resolver: "resolvers.Resolver", placeholder_type: PlaceholderType
) -> Any:
    placeholder_func = _placeholders[placeholder_type]
    return placeholder_func(resolver)


def _create_explicit_resolver_placeholder(resolver: "resolvers.Resolver") -> str:
    """Creates a placeholder value to be substituted for the resolved value when placeholders are
    allowed and the value cannot be resolved.

    The placeholder will look like one of:
      * { !ClassName } -> used when there is no argument
      * { !ClassName(argument) } -> used when there is a string argument
      * { !ClassName({'key': 'value'}) } -> used when there is a dict argument

    :param resolver: The resolver to create a placeholder for
    :return: The placeholder value
    """
    return f"{{ {resolver} }}"


def _create_alphanumeric_placeholder(resolver: "resolvers.Resolver") -> str:
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
    alphanum_placeholder = "".join(c for c in explicit_placeholder if c.isalnum())
    return alphanum_placeholder


_placeholders = {
    PlaceholderType.explicit: _create_explicit_resolver_placeholder,
    PlaceholderType.alphanum: _create_alphanumeric_placeholder,
    PlaceholderType.none: lambda resolver: None,
}
