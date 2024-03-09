from packets.packet import Packet
from construct import Byte, GreedyBytes, Prefixed, Struct

packet_0x04 = Struct(
    "passphrase" / Prefixed(Byte, GreedyBytes),
)

class Packet_0x04(Packet):
    """Respond Passphrase"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x04.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x04.build(self.struct)