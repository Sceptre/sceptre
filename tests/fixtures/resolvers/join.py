from sceptre.resolvers import Resolver


class Join(Resolver):
    def __init__(self, *args, **kwargs):
        super(Join, self).__init__(*args, **kwargs)

    def resolve(self):
        return self.argument.join(',')
