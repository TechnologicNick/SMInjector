from packets.packet import Packet
from construct import Int16ub, PascalString, Struct

packet_0x12 = Struct(
    "type" / PascalString(Int16ub, "utf8"),
    "message" / PascalString(Int16ub, "utf8"),
)

class Packet_0x12(Packet):
    """Display Message"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x12.parse(self.data)
        return self.struct
    
    def modify_packet(self):
        # self.struct.type = "<WARNING>"
        # self.struct.message = "WARNING_TUNNELING"
        pass
    
    def build_packet(self):
        rebuilt = packet_0x12.build(self.struct)
        print(rebuilt)
        return rebuilt
