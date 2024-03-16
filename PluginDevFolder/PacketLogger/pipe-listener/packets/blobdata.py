import enum
from uuid import UUID
from construct import Byte, GreedyBytes, Int16ub, Int32ub, Int32ul, Int64ub, PascalString, Prefixed, Select, Struct, Switch, this
from packets.construct_utils import CompressedLZ4Block, UuidBE
from packets.lua_object import LuaObject
from packets.packet_0x09 import CharacterCustomization


class BlobDataUids(enum.Enum):
    GenericData_World = UUID("3ff36c8b-93f7-4428-ae4d-429a6f0cf77d")
    GenericData_GameplayOptions = UUID("44ac020c-aec7-4f8b-b230-34d2e3bd23eb")
    GenericData_PlayerData = UUID("51868883-d2d2-4953-9135-1ab0bdc2a47e")

    ScriptData_Unknown = UUID("61aa13d7-e715-4153-a269-4d338c0c5bd4")
    # These UUIDv5s are probably generated from the namespace and scriptTypeID enums
    ScriptData_Game = UUID("dddc241a-2077-5a5d-920c-ba416ee1520f")
    ScriptData_Player = UUID("6ea49f8f-4c5e-5993-bf03-e8e1e93ac034")

World = Struct(
    "seed" / Int32ub,
    "filename" / PascalString(Int16ub, "utf8"),
    "classname" / PascalString(Int16ub, "utf8"),
    "terrain_params" / PascalString(Int16ub, "utf8"),
)

GameplayOptions = PascalString(Int16ub, "utf8")

PlayerData = Struct(
    "character_id" / Int32ub,
    "steam_id_64" / Int64ub,
    "inventory_container_id" / Int32ub,
    "carry_container_id" / Int32ub,
    "minus_one" / Int32ub,
    "zero_or_one_or_two" / Byte,
    "name" / PascalString(Byte, "utf8"),
    "character_customization" / CharacterCustomization,
)

BlobData = Struct(
    "uid" / UuidBE,
    "key" / Prefixed(Int16ub, Select(
        LuaObject,
        Int32ul,
        GreedyBytes,
    )),
    "world_id" / Int16ub,
    "flags" / Int32ul,
    "data" / Prefixed(Byte, CompressedLZ4Block(
        Switch(this.uid, {
            str(BlobDataUids.GenericData_World.value): World,
            str(BlobDataUids.GenericData_GameplayOptions.value): GameplayOptions,
            str(BlobDataUids.GenericData_PlayerData.value): PlayerData,
            str(BlobDataUids.ScriptData_Unknown.value): LuaObject,
            str(BlobDataUids.ScriptData_Game.value): LuaObject,
            str(BlobDataUids.ScriptData_Player.value): LuaObject,
        }, default=GreedyBytes)
    )),
)