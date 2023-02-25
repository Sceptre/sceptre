from sceptre.resolvers import NestableResolver


class Substitute(NestableResolver):
    def resolve(self):
        super().resolve()

        template, variables = self.argument
        return template.format(**variables)
