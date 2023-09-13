from packets.packet import Packet
from construct import GreedyBytes, Struct, Int32ub
import lz4.block

packet_0x2D = Struct(
    "lift_id" / Int32ub,
    "uncompressed_size" / Int32ub,
    "compressed_size" / Int32ub,
    "compressed_data" / GreedyBytes,
)

class Packet_0x2D(Packet):
    """Lift Import Creation"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x2D.parse(self.data)

        self.blueprint = lz4.block.decompress(
            self.struct.compressed_data,
            uncompressed_size=self.struct.uncompressed_size
        )

        return self.struct
    
    def modify_packet(self, direction):
        # self.struct.lift_id = 522
        # self.blueprint = b'{"bodies":[{"childs":[{"bounds":{"x":1,"y":1,"z":1},"color":"8D8F89","pos":{"x":-2,"y":0,"z":2},"shapeId":"a6c6ce30-dd47-4587-b475-085d55c6a3b4","xaxis":1,"zaxis":3}]}],"version":4}'
        pass
    
    def build_packet(self):
        self.struct.uncompressed_size = len(self.blueprint)
        # The size must not be prepended to the compressed data here, it is already stored in the packet.
        self.struct.compressed_data = lz4.block.compress(self.blueprint, store_size=False)
        self.struct.compressed_size = len(self.struct.compressed_data)

        return packet_0x2D.build(self.struct)
