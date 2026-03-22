from packets.packet import Packet
from packets.construct_utils import CompressedLZ4Block
from construct import GreedyBytes, Prefixed, Rebuild, Struct, Int32ub, this

packet_0x2D = Struct(
    "lift_id" / Int32ub,
    "uncompressed_size" / Rebuild(Int32ub, lambda this: len(this.blueprint)),
    "blueprint" / Prefixed(Int32ub, CompressedLZ4Block(GreedyBytes, uncompressed_size=this.uncompressed_size)),
)

class Packet_0x2D(Packet):
    """Lift Import Creation"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x2D.parse(self.data)
        return self.struct
    
    def modify_packet(self, direction):
        # self.struct.lift_id = 522
        # self.struct.blueprint = b'{"bodies":[{"childs":[{"bounds":{"x":1,"y":1,"z":1},"color":"8D8F89","pos":{"x":-2,"y":0,"z":2},"shapeId":"a6c6ce30-dd47-4587-b475-085d55c6a3b4","xaxis":1,"zaxis":3}]}],"version":4}'
        pass
    
    def build_packet(self):
        return packet_0x2D.build(self.struct)
