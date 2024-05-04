from packets.packet_0x01 import Packet_0x01
from packets.packet_0x02 import Packet_0x02
from packets.packet_0x03 import Packet_0x03
from packets.packet_0x04 import Packet_0x04
from packets.packet_0x05 import Packet_0x05
from packets.packet_0x06 import Packet_0x06
from packets.packet_0x07 import Packet_0x07
from packets.packet_0x08 import Packet_0x08
from packets.packet_0x09 import Packet_0x09
from packets.packet_0x0A import Packet_0x0A
from packets.packet_0x0B import Packet_0x0B
from packets.packet_0x0D import Packet_0x0D
from packets.packet_0x12 import Packet_0x12
from packets.packet_0x13 import Packet_0x13
from packets.packet_0x15 import Packet_0x15
from packets.packet_0x16 import Packet_0x16
from packets.packet_0x17 import Packet_0x17
from packets.packet_0x18 import Packet_0x18
from packets.packet_0x19 import Packet_0x19
from packets.packet_0x1A import Packet_0x1A
from packets.packet_0x1B import Packet_0x1B
from packets.packet_0x1C import Packet_0x1C
from packets.packet_0x1E import Packet_0x1E
from packets.packet_0x1F import Packet_0x1F
from packets.packet_0x20 import Packet_0x20
from packets.packet_0x21 import Packet_0x21
from packets.packet_0x22 import Packet_0x22
from packets.packet_0x23 import Packet_0x23
from packets.packet_0x27 import Packet_0x27
from packets.packet_0x2B import Packet_0x2B
from packets.packet_0x2C import Packet_0x2C
from packets.packet_0x2D import Packet_0x2D
from packets.packet_0x33 import Packet_0x33
from packets.packet_0x34 import Packet_0x34
from packets.packet_0x38 import Packet_0x38
from packets.packet_0xXX import Packet_0xXX

class PacketRegistry:
    def __init__(self):
        self.packets = {
            0x01: Packet_0x01,
            0x02: Packet_0x02,
            0x03: Packet_0x03,
            0x04: Packet_0x04,
            0x05: Packet_0x05,
            0x06: Packet_0x06,
            0x07: Packet_0x07,
            0x08: Packet_0x08,
            0x09: Packet_0x09,
            0x0A: Packet_0x0A,
            0x0B: Packet_0x0B,
            0x0D: Packet_0x0D,
            0x12: Packet_0x12,
            0x13: Packet_0x13,
            0x15: Packet_0x15,
            0x16: Packet_0x16,
            0x17: Packet_0x17,
            0x18: Packet_0x18,
            0x19: Packet_0x19,
            0x1A: Packet_0x1A,
            0x1B: Packet_0x1B,
            0x1C: Packet_0x1C,
            0x1E: Packet_0x1E,
            0x1F: Packet_0x1F,
            0x20: Packet_0x20,
            0x21: Packet_0x21,
            0x22: Packet_0x22,
            0x23: Packet_0x23,
            0x27: Packet_0x27,
            0x2B: Packet_0x2B,
            0x2C: Packet_0x2C,
            0x2D: Packet_0x2D,
            0x33: Packet_0x33,
            0x34: Packet_0x34,
            0x38: Packet_0x38,
        }

    def get_packet(self, id, data):
        if id in self.packets:
            return self.packets[id](id, data)
        else:
            return Packet_0xXX(id, data)