from sceptre.resolvers import NestableResolver


class Split(NestableResolver):
    def resolve(self):
        self.resolve_argument()
        split_on, split_string = self.argument
        return split_string.split(split_on)
