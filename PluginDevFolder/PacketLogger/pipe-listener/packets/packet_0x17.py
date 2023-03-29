from packets.packet import Packet

class Packet_0x17(Packet):
    def __init__(self, id: int, data: bytes, hidden=True):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        return self.data
    