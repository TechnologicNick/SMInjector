import enum
from random import randint
from packets.hexdump import hexdump
from packets.packet import Packet
from construct import Aligned, BitsInteger, Bitwise, Byte, Bytewise, Const, Enum, Flag, Float32b, GreedyBytes, GreedyRange, HexDump, Prefixed, Struct, Int32ub, Switch, this

character = Bitwise(Aligned(8, Struct(
    "id" / Bytewise(Int32ub),
    "is_tumbling" / Flag,
    "data" / Switch(this.is_tumbling, {
        False: Struct(
            Const(0, BitsInteger(4)),
            "keys" / Struct(
                "sprint" / Flag,
                "horizontal" / Flag,
                "crawl" / Flag,
                "jump" / Flag,
            ),
            "direction" / BitsInteger(8),
            "yaw" / BitsInteger(8),
            "pitch" / BitsInteger(8), # 0 is down, 128 is up
            "position" / Struct(
                "x" / Bytewise(Float32b),
                "y" / Bytewise(Float32b),
                "z" / Bytewise(Float32b),
            ),
        ),
        True: Struct(
            "rotation" / Struct(
                "x" / Bytewise(Float32b),
                "y" / Bytewise(Float32b),
                "z" / Bytewise(Float32b),
                "w" / Bytewise(Float32b),
            ),
            "position" / Struct(
                "x" / Bytewise(Float32b),
                "y" / Bytewise(Float32b),
                "z" / Bytewise(Float32b),
            ),
            "velocity" / Struct(
                "x" / Bytewise(Float32b),
                "y" / Bytewise(Float32b),
                "z" / Bytewise(Float32b),
            ),
            "angular_velocity" / Struct(
                "x" / Bytewise(Float32b),
                "y" / Bytewise(Float32b),
                "z" / Bytewise(Float32b),
            ),
        ),
    }),

    
    "trailing" / HexDump(Bytewise(GreedyBytes)),
)))

controller = Struct(
    "id" / Int32ub,
    "..." / HexDump(GreedyBytes),
)

class NetObjType(enum.IntEnum):
    RigidBody = 0
    ChildShape = 1          # Not implemented
    Joint = 2               # Not implemented
    Controller = 3
    Container = 4           # Not implemented
    Harvestable = 5         # Not implemented
    Character = 6
    Lift = 7                # Not implemented
    Tool = 8                # Not implemented
    Portal = 9              # Not implemented
    PathNode = 10           # Not implemented
    Unit = 11               # Not implemented
    VoxelTerrainCell = 12   # Not implemented
    ScriptableObject = 13   # Not implemented
    ShapeGroup = 14         # Not implemented

update = Struct(
    "type" / Enum(Byte, NetObjType),
    "data" / Switch(this.type, {
        "Controller": controller,
        "Character": character,
    }, default=HexDump(GreedyBytes)),
)

packet_0x18 = Struct(
    "server_tick" / Int32ub,
    "current_tick" / Int32ub,
    "bitshit" / GreedyRange(Prefixed(Byte, update, includelength=True)),
    "trailing" / HexDump(GreedyBytes),
)

class Packet_0x18(Packet):
    """Unreliable Update"""

    def __init__(self, id: int, data: bytes, hidden=True):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x18.parse(self.data)

    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x18.build(self.struct)
