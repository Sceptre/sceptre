from sceptre.resolvers import Resolver


class Join(Resolver):
    """This resolver allows you to join multiple strings together to form a single string. This is
    great for combining the outputs of multiple resolvers. This resolver works just like
    CloudFormation's ``!Join`` intrinsic function.

    The argument for this resolver should be a list with two elements: (1) A string to join the
    elements on and (2) a list of items to join.

    Example:

       parameters:
         BaseUrl: !join
           - ":"
           - - !stack_output my/app/stack.yaml::HostName
             - !stack_output my/other/stack.yaml::Port

    """

    def resolve(self):
        error_message = (
            "The argument to !join must be a 2-element list, where the first element is the join "
            "string and the second is a list of items to join."
        )
        if not isinstance(self.argument, list) or len(self.argument) != 2:
            self.raise_invalid_argument_error(error_message)

        delimiter, items_list = self.argument
        if not isinstance(delimiter, str) or not isinstance(items_list, list):
            self.raise_invalid_argument_error(error_message)

        string_items = map(str, items_list)
        joined = delimiter.join(string_items)
        return joined
