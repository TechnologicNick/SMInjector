from packets.construct_utils import Base64Encoded, CompressedLZ4Block
from construct import Aligned, Array, Bitwise, Byte, Bytewise, Const, Enum, Flag, Float32b, GreedyBytes, Int16sb, Int32sb, Int32ub, Int8sb, LazyBound, Prefixed, Rebuild, Struct, Switch, len_, this
import enum

class LuaSaveDataType(enum.IntEnum):
    Nil = 1
    Boolean = 2
    Number = 3
    String = 4
    Table = 5
    Int32 = 6
    Int16 = 7
    Int8 = 8
    Json = 9
    Userdata = 100
    Unknown_101 = 101

LuaSaveData = Struct(
    "type" / Enum(Bytewise(Byte), LuaSaveDataType),
    "value" / Switch(this.type, {
        "Nil": Const(b""),
        "Boolean": Flag,
        "Number": Bytewise(Float32b),
        "String": Bytewise(Prefixed(Int32ub, GreedyBytes)),
        "Table": Struct(
            "count" / Rebuild(Bytewise(Int32ub), len_(this.value.items)),
            "is_array" / Flag,
            "value" / Switch(this.is_array, {
                False: Struct(
                    "items" / Array(this._.count,
                        Struct(
                            "key" / LazyBound(lambda: LuaSaveData),
                            "value" / LazyBound(lambda: LuaSaveData),
                        )
                    ),
                ),
                True: Struct(
                    "offset" / Bytewise(Int32ub),
                    "items" / Array(this._.count,
                        LazyBound(lambda: LuaSaveData),
                    ),
                ),
            })
        ),
        "Int32": Bytewise(Int32sb),
        "Int16": Bytewise(Int16sb),
        "Int8": Bytewise(Int8sb),
        # "Json": Int32ub,
        # "Userdata": Int32ub,
        # "Unknown_101": Int32ub,
    }, default=Bytewise(GreedyBytes)),
)

LuaObject = Struct(
    "magic_tag" / Const(b"LUA"),
    "version" / Const(1, Int32ub),
    "data" / Bitwise(Aligned(8, LuaSaveData)),
)

ControllerData = Base64Encoded(CompressedLZ4Block(LuaObject), remove_padding=True)
