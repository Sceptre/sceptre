from sceptre.resolvers import NestableResolver


class Join(NestableResolver):
    def resolve(self):
        self.resolve_argument()
        delimiter, items_list = self.argument
        joined = delimiter.join(items_list)
        return joined
