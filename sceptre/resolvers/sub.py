from sceptre.resolvers import Resolver


class Sub(Resolver):
    """This resolver allows you to create a string using Python string format syntax. This is a
    great way to combine together a number of resolver outputs into a single string. This functions
    very similarly to Cloudformation's ``!Sub`` intrinsic function.

    The argument to this resolver should be a two-element list: (1) Is the format string, using
    curly-brace templates to indicate variables, and (2) a dictionary where the keys are the format
    string's variable names and the values are the variable values.

    Example:

       parameters:
         ConnectionString: !sub
           - "postgres://{username}:{password}@{hostname}:{port}/{database}"
           - username: {{ var.username }}
             password: !ssm /my/ssm/password
             hostname: !stack_output my/database/stack.yaml::HostName
             port: !stack_output my/database/stack.yaml::Port
             database: {{var.database}}
    """

    def resolve(self):
        error_message = (
            "The argument to !sub must be a two-element list, where the first element is the "
            "a format string and the second element is a dict of values to interpolate into it."
        )
        if not isinstance(self.argument, list) or len(self.argument) != 2:
            self.raise_invalid_argument_error(error_message)

        template, variables = self.argument
        if not isinstance(template, str) or not isinstance(variables, dict):
            self.raise_invalid_argument_error(error_message)

        try:
            return template.format(**variables)
        except KeyError as e:
            self.raise_invalid_argument_error(
                f"Could not find !sub argument for {e}", e
            )
