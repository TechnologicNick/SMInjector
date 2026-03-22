import enum
from uuid import UUID
import re
from packets.construct_utils import CompressedLZ4Block, RepeatUntilEOF
from packets.packet import Packet
from construct import Byte, BytesInteger, Enum, GreedyBytes, Hex, Prefixed, Select, Struct, Int16ub, Int32ub, Int32ul, Switch, this
from packets.hexdump import hexdump
from packets.lua_object import LuaObject

class Namespace(enum.Enum):
    CLIENT_DATA = UUID("940af9b6-d4bc-4f16-9f68-e1b8d0608908")
    UNKNOWN = UUID("a0d89ac2-7867-4471-92df-c253aec58ed3")
    REMOTE_PROCEDURE_CALL = UUID("710fc7dd-30e9-4eda-a95b-49b5b471b919")
    STORAGE = UUID("7aabd00e-cb5f-4e7a-8c88-386bf709b2cf")

class ScriptTypeID(enum.Enum):
    NULL_0 = UUID("fa2d34d7-18d2-4cec-a6fd-35662a5870ed")
    INTERACTABLE_1 = UUID("e8bdb0ca-90ff-4f2f-a296-4a2e8ba72de1")
    TOOL_2 = UUID("b1668ba4-7680-4052-bb08-6af39fe81e57")
    WORLD_3 = UUID("428c04d4-c474-415f-abbb-c33426892eb8")
    GAME_4 = UUID("d5493d04-035c-4f29-9c46-f3ceeecc9324")
    CHARACTER_5 = UUID("70282349-0e5b-46e4-b9b2-608b6561b2ef")
    HARVESTABLE_6 = UUID("04428a85-ee85-44f2-a534-3a63b05dd608")
    PLAYER_7 = UUID("6e4fbfbe-36d3-43de-a16b-08944bb6b0c7")
    UNIT_8 = UUID("84b266b1-c8f2-4254-bba2-1a5895485ff0")
    SCRIPTABLE_OBJECT_9 = UUID("453b3b65-e7fa-43ce-bbe8-82d1a970b87c")

def uuid5(namespace: UUID, name: UUID):
    from hashlib import sha1
    hash = sha1(namespace.bytes + name.bytes).digest()
    return UUID(bytes=hash[:16], version=5)

def getEnumName(namespace: Namespace, scriptTypeID: ScriptTypeID):
    return {
        "namespace": namespace.name,
        "scriptTypeID": scriptTypeID.name,
        "uuid": uuid5(namespace.value, scriptTypeID.value),
    }.__repr__()

# Dict storing cartesian product of all namespaces with scriptTypeIDs
uuidToNamespaceScriptType = {
    getEnumName(namespace, scriptTypeID): int.from_bytes(uuid5(namespace.value, scriptTypeID.value).bytes) for namespace in Namespace for scriptTypeID in ScriptTypeID
}

ClientData = Struct(
    "script_type_id" / Enum(Byte, ScriptTypeID),
    "data" / LuaObject,
)

RemoteProcedureCall = Struct(
    "callback_name" / Prefixed(Byte, GreedyBytes),
    "unknown" / Byte,
    "lua_data" / LuaObject,
)

BlobData = Struct(
    "uid" / Enum(BytesInteger(16), **uuidToNamespaceScriptType),
    "key" / Prefixed(Int16ub, Select(
        LuaObject,
        Int32ul,
        GreedyBytes,
    )),
    "world_id" / Int16ub,
    "flags" / Byte,
    "data" / Prefixed(Int32ub, CompressedLZ4Block(Switch(lambda ctx: re.search("'namespace': '(.*?)'", ctx.uid).group(1), {
        Namespace.CLIENT_DATA.name: ClientData,
        Namespace.REMOTE_PROCEDURE_CALL.name: RemoteProcedureCall,
    }, default=GreedyBytes))),
)

packet_0x19 = Struct(
    "tick" / Int32ub,
    "blob_data" / RepeatUntilEOF(BlobData),
)

class Packet_0x19(Packet):
    """Script Data (Server -> Client)"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x19.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass

    def build_packet(self):
        return packet_0x19.build(self.struct)
