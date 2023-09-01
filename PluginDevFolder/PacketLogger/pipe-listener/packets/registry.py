from packets.packet_0x12 import Packet_0x12
from packets.packet_0x13 import Packet_0x13
from packets.packet_0x16 import Packet_0x16
from packets.packet_0x17 import Packet_0x17
from packets.packet_0x18 import Packet_0x18
from packets.packet_0x1E import Packet_0x1E
from packets.packet_0x1F import Packet_0x1F
from packets.packet_0x20 import Packet_0x20
from packets.packet_0x22 import Packet_0x22
from packets.packet_0x2B import Packet_0x2B
from packets.packet_0x2C import Packet_0x2C
from packets.packet_0x2D import Packet_0x2D
from packets.packet_0x34 import Packet_0x34
from packets.packet_0x38 import Packet_0x38
from packets.packet_0xXX import Packet_0xXX

class PacketRegistry:
    def __init__(self):
        self.packets = {
            0x12: Packet_0x12,
            0x13: Packet_0x13,
            0x16: Packet_0x16,
            0x17: Packet_0x17,
            0x18: Packet_0x18,
            0x1E: Packet_0x1E,
            0x1F: Packet_0x1F,
            0x20: Packet_0x20,
            0x22: Packet_0x22,
            0x2B: Packet_0x2B,
            0x2C: Packet_0x2C,
            0x2D: Packet_0x2D,
            0x34: Packet_0x34,
            0x38: Packet_0x38,
        }

    def get_packet(self, id, data):
        if id in self.packets:
            return self.packets[id](id, data)
        else:
            return Packet_0xXX(id, data)