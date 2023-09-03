from packets.packet import Packet
from construct import Int32ub, Struct

packet_0x21 = Struct(
    "container_id" / Int32ub,
    "slot" / Int32ub,
    "quantity" / Int32ub,
)

class Packet_0x21(Packet):
    """Drop Item Stack"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x21.parse(self.data)

        return self.struct
    
    def modify_packet(self):
        pass
    
    def build_packet(self):
        return packet_0x21.build(self.struct)
    
        # quantity = self.struct.quantity

        # self.struct.quantity = 1
        
        # packets = []
        # for i in range(100):
        #     self.struct.container_id = i
        #     packets.append(packet_0x21.build(self.struct))

        # return [packet_0x21.build(self.struct)] * quantity
        # return packets
    