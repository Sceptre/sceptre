from sceptre.resolvers import NestableResolver


class Substitute(NestableResolver):
    def resolve(self):
        self.resolve_argument()
        template, variables = self.argument
        return template.format(**variables)
