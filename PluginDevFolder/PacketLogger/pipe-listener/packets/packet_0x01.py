from packets.packet import Packet
from construct import Struct

packet_0x01 = Struct(
)

class Packet_0x01(Packet):
    """Hello"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x01.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x01.build(self.struct)