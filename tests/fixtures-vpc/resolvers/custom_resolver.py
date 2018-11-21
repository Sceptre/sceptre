from sceptre.resolvers import Resolver


class CustomResolver(Resolver):
    def __init__(self, *args, **kwargs):
        super(CustomResolver, self).__init__(*args, **kwargs)

    def resolve(self):
        return "value"
