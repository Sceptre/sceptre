from sceptre.resolvers import Resolver


class NoValue(Resolver):
    """This resolver resolves to nothing, functioning just like the AWS::NoValue special value. When
    assigned to a resolvable Stack property, it will remove the config key/value from the stack or
    the container on the stack where it has been assigned, as if this value wasn't assigned at all.

    This is mostly useful for simplifying conditional logic on Stack and StackGroup config files
    where, if a certain condition is met, a value is passed, otherwise it's not passed at all.
    """

    def resolve(self) -> None:
        return None
