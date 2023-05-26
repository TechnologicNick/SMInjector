def class_to_dict(cls, exclude_keys=["_io"]):
    """Recursively converts class attributes to a dictionary."""
    d = {}
    for k in cls.keys():
        if k not in exclude_keys:
            attr = getattr(cls, k)
            if isinstance(attr, type):
                d[k] = class_to_dict(attr, exclude_keys)
            else:
                d[k] = attr
    return d
