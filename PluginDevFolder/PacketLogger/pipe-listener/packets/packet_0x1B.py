from packets.packet import Packet
from packets.blobdata import BlobData
from packets.construct_utils import RepeatUntilEOF
from construct import Int32ub, Struct

packet_0x1B = Struct(
    "game_tick" / Int32ub,
    "blob_data" / RepeatUntilEOF(BlobData),
)

class Packet_0x1B(Packet):
    """Generic Data (Server -> Client)"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x1B.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x1B.build(self.struct)