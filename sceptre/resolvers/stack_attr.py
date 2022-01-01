from sceptre.resolvers import Resolver


class StackAttr(Resolver):

    # These are all the attributes on Stack Configs whose names are changed when they are assigned
    # to the Stack instance.
    STACK_ATTR_MAP = {
        'template': 'template_handler_config',
        'protect': 'protected',
        'stack_name': 'external_name',
        'stack_tags': 'tags'
    }

    def resolve(self):
        segments = self.argument.split('.')
        # Remap top-level attributes to match stack config
        segments[0] = self.STACK_ATTR_MAP.get(segments[0], segments[0])

        result = self._recursively_resolve_segments(self.stack, segments)
        return result

    def _recursively_resolve_segments(self, obj, segments):
        if not segments:
            return obj

        attr_name, *rest = segments
        if isinstance(obj, dict):
            value = obj[attr_name]
        elif isinstance(obj, list):
            value = obj[int(attr_name)]
        else:
            value = getattr(obj, attr_name)

        return self._recursively_resolve_segments(value, rest)
