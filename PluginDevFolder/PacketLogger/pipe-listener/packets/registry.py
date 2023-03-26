from packets.packet_0x18 import Packet_0x18
from packets.packet_0x1E import Packet_0x1E
from packets.packet_0xXX import Packet_0xXX

class PacketRegistry:
    def __init__(self):
        self.packets = {
            0x18: Packet_0x18,
            0x1E: Packet_0x1E,
        }

    def get_packet(self, id, data):
        if id in self.packets:
            return self.packets[id](id, data)
        else:
            return Packet_0xXX(id, data)