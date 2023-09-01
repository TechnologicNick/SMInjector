from packets.packet import Packet
from construct import Byte, BytesInteger, Enum, Hex, Int32sb, Int32ub, NamedTuple, Struct, Switch, this

vec3i = NamedTuple("vec3i", "z y x", Int32sb[3])

uuid = Hex(BytesInteger(16, swapped=True))

packet_0x23 = Struct(
    "local_pos_high" / vec3i,
    "local_pos_low" / vec3i,
    "removed_from_type" / Enum(Byte, BODY = 4, LIFT = 6),
    "removed_from" / Switch(this.removed_from_type, {
        "BODY": Struct(
            "shape_id" / Int32ub,
            "body_id" / Int32ub,
        ),
        "LIFT": Struct(
            "unknown_0x00" / Hex(BytesInteger(4)),
            "lift_id" / Int32ub,
        ),
    }),
)

class Packet_0x23(Packet):
    """Remove"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x23.parse(self.data)

        return self.struct
    
    def modify_packet(self):
        # if self.struct.removed_from_type == "BODY":
        #     (z, y, x) = self.struct.local_pos_low
        #     self.struct.local_pos_low = (z-50, y-50, x-50)
        #     (z, y, x) = self.struct.local_pos_high
        #     self.struct.local_pos_high = (z+50, y+50, x+50)
        pass
    
    def build_packet(self):
        return packet_0x23.build(self.struct)
    