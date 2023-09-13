from packets.packet import Packet
from construct import Struct, Int32ub

packet_0x2B = Struct(
    "lift_id" / Int32ub,
)

class Packet_0x2B(Packet):
    """Lift Delete Creation"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x2B.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        # self.struct.lift_id = 522
        pass
    
    def build_packet(self):
        return packet_0x2B.build(self.struct)
