from sceptre.resolvers import Resolver


class Select(Resolver):
    """This resolver allows you to select a specific index of a list of items. This is great for combining
    with the ``!split`` resolver to obtain part of a string. This function works almost the same as
    CloudFormation's ``!Select`` intrinsic function, **except you can use this with negative indexes to
    select with a reverse index**.

    The argument for this resolver should be a list with two elements: (1) A numerical index and (2) a
    list of items to select out of. If the index is negative, it will select from the end of the list.
    For example, "-1" would select the last element and "-2" would select the second-to-last element.

    Example:

       parameters:
         # This selects the last element after you split the connection string on "/"
         DatabaseName: !select
           - -1
           - !split ["/", !stack_output my/database/stack.yaml::ConnectionString]
    """

    def resolve(self):
        index, items = self.argument
        return items[index]
