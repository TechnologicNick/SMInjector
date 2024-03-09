import enum
from packets.packet import Packet
from packets.construct_utils import Uuid, UuidBE
from construct import Bitwise, Enum, Flag, GreedyBytes, Int16ub, Int32ub, Padding, Prefixed, PrefixedArray, Struct

class GameMode(enum.IntEnum):
    AlphaTerrain = 0
    FlatTerrain = 1
    ClassicTerrain = 2
    CreatedTerrain_Test = 3
    CreatedTerrain = 4
    Challenge = 5
    ChallengeBuilder = 6
    Terrain = 7
    MenuCreation = 8
    Survival = 14
    Custom = 15
    Development = 16

UserGeneratedContent = Struct(
    "file_id" / Int32ub,
    "local_id" / Uuid,
)

GenericData = Struct(
    "uuid" / UuidBE,
    "size" / Int16ub,
    "key" / Int32ub,
)

packet_0x02 = Struct(
    "version" / Int32ub,
    "gamemode" / Enum(Int32ub, GameMode),
    "seed" / Int32ub,
    "gametick" / Int32ub,
    "user_generated_content" / PrefixedArray(Int32ub, UserGeneratedContent),
    "unknown_data" / Prefixed(Int16ub, GreedyBytes),
    "script_data" / PrefixedArray(Int32ub, GenericData),
    "generic_data" / PrefixedArray(Int32ub, GenericData),
    "flags" / Bitwise(Struct(
        "developer_mode" / Flag,
        Padding(7),
    )),
)

class Packet_0x02(Packet):
    """Server Info"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x02.parse(self.data)

        print(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x02.build(self.struct)