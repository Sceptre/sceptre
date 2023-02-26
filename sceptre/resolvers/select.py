from sceptre.resolvers import Resolver


class Select(Resolver):
    def resolve(self):
        index, items = self.argument
        return items[index]
