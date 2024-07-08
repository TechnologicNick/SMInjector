from packets.packet import Packet
from packets.construct_utils import RepeatUntilEOF
from construct import Byte, GreedyBytes, Int32ub, Prefixed, Struct

packet_0x1D = Struct(
    "packets" / RepeatUntilEOF(
        Prefixed(Int32ub, Struct(
            "packet_id" / Byte,
            "data" / GreedyBytes,
        )),
    ),
)

class Packet_0x1D(Packet):
    """Compound Packet"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x1D.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x1D.build(self.struct)
