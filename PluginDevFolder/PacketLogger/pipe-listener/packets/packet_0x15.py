from packets.packet import Packet
from packets.packet_0x16 import packet_0x16

packet_0x15 = packet_0x16

class Packet_0x15(Packet):
    """Initialization Network Update"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x15.parse(self.data)
        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return self.data
        # return packet_0x15.build(self.struct)
