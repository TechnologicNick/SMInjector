import base64
import itertools
from uuid import UUID
from construct import Adapter, BytesInteger, Construct, ExplicitError, GreedyBytes, ListContainer, SizeofError, StopFieldError, StringError, Subconstruct, Tunnel, stream_seek, stream_tell, unicodestringtype

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
        if callable(self.uncompressed_size):
            uncompressed_size = self.uncompressed_size(context, path)
        else:
            uncompressed_size = self.uncompressed_size

        print(uncompressed_size)

        return self.lib.decompress(data, uncompressed_size=uncompressed_size)

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
        return str(UUID(int=obj))

    def _encode(self, obj, context, path):
        return UUID(obj).int

Uuid = UuidAdapter(BytesInteger(16, swapped=True))

UuidBE = UuidAdapter(BytesInteger(16, swapped=False))
"""The bytes are in the same order as the UUID string representation."""

class RepeatUntilEOF(Subconstruct):
    r"""
    Homogenous array of elements, similar to C# generic IEnumerable<T>, but works with unknown count of elements by parsing until end of stream.

    Parses into a ListContainer (a list). Parsing stops when an exception occured when parsing the subcon, either due to EOF or subcon format not being able to parse the data. Either way, when RepeatUntilEOF encounters either failure, it raises the error. Builds from enumerable, each element as-is. Size is undefined.

    This class supports stopping. If :class:`~construct.core.StopIf` field is a member, and it evaluates its lambda as positive, this class ends parsing or building as successful without processing further fields.

    :param subcon: Construct instance, subcon to process individual elements
    :param discard: optional, bool, if set then parsing returns empty list

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises StreamError: stream is not seekable and tellable

    Can propagate any exception from the lambdas, possibly non-ConstructError.

    Example::

        >>> d = RepeatUntilEOF(Byte)
        >>> d.build(range(8))
        b'\x00\x01\x02\x03\x04\x05\x06\x07'
        >>> d.parse(_)
        [0, 1, 2, 3, 4, 5, 6, 7]
    """

    def __init__(self, subcon, discard=False):
        super().__init__(subcon)
        self.discard = discard

    def _parse(self, stream, context, path):
        discard = self.discard
        obj = ListContainer()
        try:
            current = stream_tell(stream, path)
            end = stream_seek(stream, 0, 2, path)
            stream_seek(stream, current, 0, path)

            for i in itertools.count():
                if stream_tell(stream, path) >= end:
                    break

                context._index = i
                e = self.subcon._parsereport(stream, context, path)
                if not discard:
                    obj.append(e)
        except StopFieldError:
            pass
        except ExplicitError:
            raise
        return obj

    def _build(self, obj, stream, context, path):
        discard = self.discard
        try:
            retlist = ListContainer()
            for i,e in enumerate(obj):
                context._index = i
                buildret = self.subcon._build(e, stream, context, path)
                if not discard:
                    retlist.append(buildret)
            return retlist
        except StopFieldError:
            pass

    def _sizeof(self, context, path):
        raise SizeofError(path=path)

    def _emitfulltype(self, ksy, bitwise):
        return dict(type=self.subcon._compileprimitivetype(ksy, bitwise), repeat="eos")
    
class PaddingUntilAligned(Construct):
    r"""
    Reads until the stream is aligned to a multiple of the given size. This is useful for reading padding bytes.

    Parses into a bytes object. Parsing stops when the stream is aligned to multiple of the given size. Builds from bytes object. Size is undefined.

    This class supports stopping. If :class:`~construct.core.StopIf` field is a member, and it evaluates its lambda as positive, this class ends parsing or building as successful without processing further fields.

    :param alignment: int, size of alignment

    :raises StreamError: requested reading negative amount, could not read enough bytes, requested writing different amount than actual data, or could not write all bytes
    :raises StreamError: stream is not tellable

    Can propagate any exception from the lambdas, possibly non-ConstructError.

    Example::

        >>> d = PaddingUntilAligned(4)
        >>> d.build(b"")
        b''
        >>> d.parse(b"\x00\x00\x00")
        b''
        >>> d = Sequence(Byte, PaddingUntilAligned(4), Byte)
        >>> d.build([1,b"",2])
        b'\x01\x00\x00\x00\x02'
        >>> d.parse(_)
        [1, b'\x00\x00\x00', 2]
    """

    def __init__(self, alignment):
        super().__init__()
        self.alignment = alignment

    def _parse(self, stream, context, path):
        current = stream_tell(stream, path)
        end = (current + self.alignment - 1) // self.alignment * self.alignment
        return stream.read(end - current)
    
    def _build(self, obj, stream, context, path):
        if obj is not None:
            stream.write(obj)
        current = stream_tell(stream, path)
        end = (current + self.alignment - 1) // self.alignment * self.alignment
        if end > current:
            stream.write(b"\x00" * (end - current))
        return obj
