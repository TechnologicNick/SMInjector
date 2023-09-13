from packets.hexdump import hexdump
from packets.packet import Packet
from construct import Byte, FlagsEnum, Struct, Int32ub
from enum import IntFlag

class ConnectFlags(IntFlag):
    PART = 0x01
    BEARING = 0x02

    CONNECT = 0x10
    DISCONNECT = 0x20
    CHANGE_DIRECTION = 0x40

packet_0x2C = Struct(
    "child_id" / Int32ub,
    "parent_id" / Int32ub,
    "flags" / FlagsEnum(Byte, ConnectFlags),
)

class Packet_0x2C(Packet):
    """Connect"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x2C.parse(self.data)

        print(hexdump(self.data))

        return self.struct
    
    def modify_packet(self, direction):
        # self.struct.child_id = 24
        # self.struct.parent_id = 26
        # self.struct.flags = ConnectFlags.CONNECT | ConnectFlags.DISCONNECT | ConnectFlags.PART
        pass
    
    def build_packet(self):
        return packet_0x2C.build(self.struct)
