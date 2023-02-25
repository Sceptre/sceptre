from sceptre.resolvers import NestableResolver


class Substitute(NestableResolver):
    def resolve(self):
        template, variables = self.argument
        return template.format(**variables)
