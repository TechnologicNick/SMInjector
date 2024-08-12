from packets.packet import Packet

class Packet_0xXX(Packet):
    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        return self.data
