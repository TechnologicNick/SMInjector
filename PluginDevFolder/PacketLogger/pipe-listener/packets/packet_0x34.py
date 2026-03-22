from packets.packet import Packet
from construct import Struct, Int32sb, Int32ub

packet_0x34 = Struct(
    "lift_id" / Int32ub,
    "level_change" / Int32sb,
)

class Packet_0x34(Packet):
    """Lift Level"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x34.parse(self.data)
        return self.struct
    
    def modify_packet(self, direction):
        # self.struct.lift_id = 1
        # self.struct.level_change *= 2
        pass
    
    def build_packet(self):
        return packet_0x34.build(self.struct)
