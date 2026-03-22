from packets.packet import Packet
from construct import Int32ul, Struct

packet_0x08 = Struct(
    "index" / Int32ul,
)

class Packet_0x08(Packet):
    """Checksums Denied"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x08.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x08.build(self.struct)