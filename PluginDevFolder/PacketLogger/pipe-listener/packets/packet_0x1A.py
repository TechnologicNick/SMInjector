from packets.packet import Packet
from construct import Struct
from packets.hexdump import hexdump
from packets.construct_utils import RepeatUntilEOF
from packets.packet_0x19 import rpc

packet_0x1A = Struct(
    "rpcs" / RepeatUntilEOF(rpc),
)

class Packet_0x1A(Packet):
    """Lua Remote Procedure Call (Client -> Server)"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        # print(self.data)
        self.struct = packet_0x1A.parse(self.data)

        # print(self.struct)

        return hexdump(self.data)
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x1A.build(self.struct)
