from sceptre.resolvers import Resolver


class Substitute(Resolver):
    def resolve(self):
        template, variables = self.argument
        return template.format(**variables)
