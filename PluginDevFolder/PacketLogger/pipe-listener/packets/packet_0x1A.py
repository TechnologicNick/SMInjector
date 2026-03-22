from packets.packet import Packet
from construct import Struct
from packets.construct_utils import RepeatUntilEOF
from packets.packet_0x19 import BlobData

packet_0x1A = Struct(
    "blob_data" / RepeatUntilEOF(BlobData),
)

class Packet_0x1A(Packet):
    """Script Data (Client -> Server)"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x1A.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x1A.build(self.struct)
