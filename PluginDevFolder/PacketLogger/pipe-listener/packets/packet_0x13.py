from packets.packet import Packet
from construct import Int16ub, GreedyString, Rebuild, Struct

packet_0x13 = Struct(
    "length" / Rebuild(Int16ub, lambda this: len(this.message.encode("utf8"))),
    "message" / GreedyString("utf8"),
)

class Packet_0x13(Packet):
    """Display Alert Text"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x13.parse(self.data)
        return self.struct
    
    def modify_packet(self):
        # self.struct.message = "balls"
        pass
    
    def build_packet(self):
        rebuilt = packet_0x13.build(self.struct)
        print(rebuilt)
        return rebuilt
