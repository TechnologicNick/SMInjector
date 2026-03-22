from packets.packet import Packet
from packets.blobdata import BlobData
from packets.construct_utils import RepeatUntilEOF
from construct import Int32ub, Struct

packet_0x0B = Struct(
    "game_tick" / Int32ub,
    "blob_data" / RepeatUntilEOF(BlobData),
)

class Packet_0x0B(Packet):
    """Script Initialization Data"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x0B.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return self.data
        # return packet_0x0A.build(self.struct)