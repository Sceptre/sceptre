from sceptre.resolvers import Resolver


class Split(Resolver):
    """This resolver will split a value on a given delimiter string. This is great when combining with the
    ``!select`` resolver. This function works the same as CloudFormation's ``!Split`` intrinsic function.

    Note: The return value of this resolver is a *list*, not a string. This will not work to set Stack
    configurations that expect strings, but it WILL work to set Stack configurations that expect lists.

    The argument for this resolver should be a list with two elements: (1) The delimiter to split on and
    (2) a string to split.

    Example:
       notifications: !split
         - ";"
         - !stack_output my/sns/topics.yaml::SemicolonDelimitedArns
    """

    def resolve(self):
        split_on, split_string = self.argument
        return split_string.split(split_on)
