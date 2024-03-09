import base64
from uuid import UUID
from construct import Adapter, BytesInteger, GreedyBytes, StringError, Tunnel, unicodestringtype

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
    
class StringEncodedEx(Adapter):
    """Used internally."""

    def __init__(self, subcon, encoding, errors="strict"):
        super().__init__(subcon)
        if not encoding:
            raise StringError("String* classes require explicit encoding")
        self.encoding = encoding
        self.errors = errors

    def _decode(self, obj: bytes, context, path):
        return obj.decode(self.encoding, errors=self.errors)

    def _encode(self, obj, context, path):
        if not isinstance(obj, unicodestringtype):
            raise StringError("string encoding failed, expected unicode string", path=path)
        if obj == u"":
            return b""
        return obj.encode(self.encoding, errors=self.errors)

    def _emitparse(self, code):
        return f"({self.subcon._compileparse(code)}).decode({repr(self.encoding)}, errors={repr(self.errors)})"

    def _emitbuild(self, code):
        raise NotImplementedError
        # This is not a valid implementation. obj.encode() should be inserted into subcon
        # return f"({self.subcon._compilebuild(code)}).encode({repr(self.encoding)})"

def GreedyStringEx(encoding, errors="strict"):
    r"""
    String that reads entire stream until EOF, and writes a given string as-is. Analog to :class:`~construct.core.GreedyBytes` but also applies unicode-to-bytes encoding.

    :param encoding: string like: utf8 utf16 utf32 ascii

    :raises StringError: building a non-unicode string
    :raises StreamError: stream failed when reading until EOF

    Example::

        >>> d = GreedyString("utf8")
        >>> d.build(u"Афон")
        b'\xd0\x90\xd1\x84\xd0\xbe\xd0\xbd'
        >>> d.parse(_)
        u'Афон'
    """
    macro = StringEncodedEx(GreedyBytes, encoding, errors)
    def _emitfulltype(ksy, bitwise):
        return dict(size_eos=True, type="str", encoding=encoding, errors=errors)
    macro._emitfulltype = _emitfulltype
    return macro

class Base64Encoded(Tunnel):
    def __init__(self, subcon, remove_padding=False):
        super().__init__(subcon)
        self.remove_padding = remove_padding

    def _decode(self, data, context, path):
        return base64.b64decode(data + b"==")

    def _encode(self, data, context, path):
        encoded = base64.b64encode(data)
        if self.remove_padding:
            encoded = encoded.rstrip(b"=")
        return encoded

class UuidAdapter(Adapter):
    def _decode(self, obj, context, path):
        print(obj)
        return str(UUID(int=obj))

    def _encode(self, obj, context, path):
        return UUID(obj).int

Uuid = UuidAdapter(BytesInteger(16, swapped=True))

UuidBE = UuidAdapter(BytesInteger(16, swapped=False))
"""The bytes are in the same order as the UUID string representation."""