def list_join(a, b):
    if a and not isinstance(a, list):
        raise TypeError('{} is not a list'.format(a))
    if b and not isinstance(b, list):
        raise TypeError('{} is not a list'.format(b))

    if a is None:
        return b

    if b is not None:
        return a + b

    return a


def dict_merge(a, b):
    if a and not isinstance(a, dict):
        raise TypeError('{} is not a list'.format(a))
    if b and not isinstance(b, dict):
        raise TypeError('{} is not a list'.format(b))

    if a is None:
        return b

    if b is not None:
        a.update(b)
        return a

    return a


def child_wins(a, b):
    return b
