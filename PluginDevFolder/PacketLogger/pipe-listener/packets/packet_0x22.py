from packets.packet import Packet
from construct import Byte, BytesInteger, Enum, Hex, Int32sb, Int32ub, NamedTuple, Struct, Switch, this

vec3i = NamedTuple("vec3i", "z y x", Int32sb[3])

uuid = Hex(BytesInteger(16, swapped=True))

packet_0x22 = Struct(
    "hotbar_index" / Int32ub,
    "total_quantity" / Int32ub,
    "size" / vec3i,
    "local_pos_start" / vec3i,
    "z_axis" / vec3i,
    "x_axis" / vec3i,
    "local_pos" / vec3i,
    "item_uuid" / uuid,
    "shape_uuid" / uuid,
    "placed_on_type" / Enum(Byte, TERRAIN_SURFACE = 2, TERRAIN_ASSET = 3, BODY = 4, LIFT = 6, JOINT = 8),
    "placed_on" / Switch(this.placed_on_type, {
        "TERRAIN_SURFACE": Struct(
            "unknown_0x00" / Hex(BytesInteger(4)),
            "unknown_0x04" / Hex(BytesInteger(4)),
        ),
        "TERRAIN_ASSET": Struct(
            "unknown_0x00" / Hex(BytesInteger(4)),
            "unknown_0x04" / Hex(BytesInteger(4)),
        ),
        "BODY": Struct(
            "shape_id" / Int32ub,
            "body_id" / Int32ub,
        ),
        "LIFT": Struct(
            "unknown_0x00" / Hex(BytesInteger(4)),
            "lift_id" / Int32ub,
        ),
        "JOINT": Struct(
            "unknown_0x00" / Hex(BytesInteger(4)),
            "joint_id" / Int32ub,
        ),
    }),
)

class Packet_0x22(Packet):
    """Place"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x22.parse(self.data)
        return self.struct
    
    def modify_packet(self, direction):
        # self.struct.size = (-3, 3, 3)
        # self.struct.x_axis = (0, 0, 1)
        # self.struct.z_axis = (1, 0, 1)
        # self.struct.shape_uuid = 0x4A1B886B913E4AADB5B66E41B0DB23A6
        # self.struct.item_uuid = 0x4A1B886B913E4AADB5B66E41B0DB23A6
        pass
    
    def build_packet(self):
        return packet_0x22.build(self.struct)
    