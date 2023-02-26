from sceptre.resolvers import Resolver


class Substitute(Resolver):
    """This resolver allows you to create a string using Python string format syntax. This is a
    great way to combine together a number of resolver outputs into a single string. This functions
    very similarly to Cloudformation's ``!Sub`` intrinsic function.

    The argument to this resolver should be a two-element list: (1) Is the format string, using
    curly-brace templates to indicate variables, and (2) a dictionary where the keys are the format
    string's variable names and the values are the variable values.

    Example:

       parameters:
         ConnectionString: !substitute
           - "postgres://{username}:{password}@{hostname}:{port}/{database}"
           - username: {{ var.username }}
             password: !ssm /my/ssm/password
             hostname: !stack_output my/database/stack.yaml::HostName
             port: !stack_output my/database/stack.yaml::Port
             database: {{var.database}}
    """

    def resolve(self):
        template, variables = self.argument
        return template.format(**variables)
