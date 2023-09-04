from construct import Tunnel

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

class CompressedLZ4Block(Tunnel):
    r"""
    Compresses and decompresses underlying stream before processing subcon. When parsing, entire stream is consumed. When building, it puts compressed bytes without marking the end. This construct should be used with :class:`~construct.core.Prefixed` .

    Parsing and building transforms all bytes using LZ4 library. Since data is processed until EOF, it behaves similar to `GreedyBytes`. Size is undefined.

    :param subcon: Construct instance, subcon used for storing the value

    :raises ImportError: needed module could not be imported by ctor
    :raises StreamError: stream failed when reading until EOF

    Can propagate lz4.block exceptions.

    Example::

        >>> d = Prefixed(VarInt, CompressedLZ4Block(GreedyBytes))
        >>> d.build(bytes(100))
        b'\x0fd\x00\x00\x00\x1f\x00\x01\x00KP\x00\x00\x00\x00\x00'
        >>> len(_)
        16
    """

    def __init__(self, subcon, uncompressed_size=0x400000):
        super().__init__(subcon)
        import lz4.block
        self.lib = lz4.block
        self.uncompressed_size = uncompressed_size

    def _decode(self, data, context, path):
        return self.lib.decompress(data, uncompressed_size=self.uncompressed_size)

    def _encode(self, data, context, path):
        return self.lib.compress(data, store_size=False)
