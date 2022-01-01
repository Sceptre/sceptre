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
        first_segment = segments[0]
        segments[0] = self.STACK_ATTR_MAP.get(first_segment, first_segment)

        if self._key_is_from_stack_group_config(first_segment):
            obj = self.stack.stack_group_config
        else:
            obj = self.stack

        result = self._recursively_resolve_segments(obj, segments)
        return result

    def _key_is_from_stack_group_config(self, key: str):
        return key in self.stack.stack_group_config and not hasattr(self.stack, key)

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
