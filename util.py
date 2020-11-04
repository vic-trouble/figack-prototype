import collections


def object_update_from(dest, source):
    """ Universal update of an object either from dict or another object.
        The source id remains unchanged. """
    dest.__dict__.update(source if isinstance(source, collections.abc.Mapping) else source.__dict__)
