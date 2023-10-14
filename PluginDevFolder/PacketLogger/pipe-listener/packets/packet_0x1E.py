from construct import Aligned, BitsInteger, Bitwise, Byte, Const, Flag, Int32ub, Struct
from packets.packet import Packet

packet_0x1E = Struct(
    "tick" / Int32ub,
    "pressed_keys" / Bitwise(Struct(
        Const(0, BitsInteger(4)),
        "sprint" / Flag,
        "horizontal" / Flag,
        "crawl" / Flag,
        "jump" / Flag,
    )),
    "direction" / Byte,
    "yaw" / Byte, # 0 = right, increases by 64 every 45 degrees counter-clockwise
    "pitch" / Byte, # 0 is down, 128 is up
)

class Packet_0x1E(Packet):
    """Player Movement"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x1E.parse(self.data)
        return self.struct

    def modify_packet(self, direction):
        # self.struct.direction = (self.struct.direction + 64) % 256
        # self.struct.yaw = (self.struct.yaw - 64) % 256
        # self.struct.pressed_keys.sprint = True
        pass
    
    def build_packet(self):
        # return self.data
        return packet_0x1E.build(self.struct)
