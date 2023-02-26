from sceptre.resolvers import Resolver


class Join(Resolver):
    def resolve(self):
        delimiter, items_list = self.argument
        joined = delimiter.join(items_list)
        return joined
