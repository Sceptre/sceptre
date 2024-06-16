from sceptre.resolvers import Resolver


class Select(Resolver):
    """This resolver allows you to select a specific index from a list of items or a specific key
    from a dict.. This is great for combining with the ``!split`` resolver to obtain part of a
    string. This function works almost the same as CloudFormation's ``!Select`` intrinsic function,
    **except (1) you can use this with negative indexes to select with a reverse index** and (2)
    you can select keys from a dict.

    The argument for this resolver should be a list with two elements: (1) A numerical index or
    string key and (2) a list or dict of items to select out of. If the index is negative,
    it will select from the end of the list. For example, "-1" would select the last element and
    "-2" would select the second-to-last element.

    Example:

       parameters:
         # This selects the last element after you split the connection string on "/"
         DatabaseName: !select
           - -1
           - !split ["/", !stack_output my/database/stack.yaml::ConnectionString]
    """

    def resolve(self):
        error_message = (
            "The argument to !select must be a two-element list, where the first element is the "
            "index or key to select with and the second element is the list or dict to select from."
        )
        if not isinstance(self.argument, list) or len(self.argument) != 2:
            self.raise_invalid_argument_error(error_message)

        index, items = self.argument
        if not isinstance(items, (dict, list)):
            self.raise_invalid_argument_error(error_message)

        try:
            return items[index]
        except (TypeError, KeyError, IndexError) as e:
            self.raise_invalid_argument_error(
                f"Could not select with index/key {index}: {e}", e
            )
