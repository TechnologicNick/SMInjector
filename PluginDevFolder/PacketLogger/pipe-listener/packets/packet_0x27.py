from packets.packet import Packet
from construct import Int32ub, Struct

packet_0x27 = Struct(
    "joint_id" / Int32ub,
)

class Packet_0x27(Packet):
    """Remove Joint"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x27.parse(self.data)

        return self.struct
    
    def modify_packet(self):
        # self.struct.joint_id = 18
        pass
    
    def build_packet(self):
        return packet_0x27.build(self.struct)
    