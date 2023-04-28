from packets.packet import Packet
from packets.types import UUID, Vec3i
from packets.hexdump import hexdump
from enum import IntEnum
import struct

class PlacedOn(IntEnum):
    TERRAIN_SURFACE = 2
    TERRAIN_ASSET = 3
    BODY = 4
    LIFT = 6
    JOINT = 8

    UNKNOWN = -1
    
    def parse_transaction(self, data: bytes):
        if self == PlacedOn.TERRAIN_SURFACE:
            return {
                "unknown_float1": struct.unpack("f", data[0:4])[0],
                "unknown_float2": struct.unpack("f", data[4:8])[0],
            }
        elif self == PlacedOn.TERRAIN_ASSET:
            return {
                "unknown_float1": struct.unpack("f", data[0:4])[0],
                "unknown_float2": struct.unpack("f", data[4:8])[0],
            }
        elif self == PlacedOn.BODY:
            return {
                "shape_id": int.from_bytes(data[0:4], byteorder="big"),
                "body_id": int.from_bytes(data[4:8], byteorder="big"),
            }
        elif self == PlacedOn.LIFT:
            return {
                "unknown_float": struct.unpack("f", data[0:4])[0],
                "lift_id": int.from_bytes(data[4:8], byteorder="big"),
            }
        elif self == PlacedOn.JOINT:
            return {
                "unknown_float": struct.unpack("f", data[0:4])[0],
                "joint_ids": int.from_bytes(data[4:8], byteorder="big"),
            }
        else:
            return hexdump(data)

class Packet_0x22(Packet):
    """Place"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        print(hexdump(self.data))
        return {
            "hotbar_index": int.from_bytes(self.data[0:4], byteorder="big"),
            "unknown_0x04": int.from_bytes(self.data[4:8], byteorder="big"),
            "size": Vec3i(self.data[8:20], byteorder="big", signed=True),
            "local_pos_start": Vec3i(self.data[20:32], byteorder="big", signed=True),
            "z_axis": Vec3i(self.data[32:44], byteorder="big", signed=True),
            "x_axis": Vec3i(self.data[44:56], byteorder="big", signed=True),
            "local_pos": Vec3i(self.data[56:68], byteorder="big", signed=True),
            "uuid": UUID(self.data[68:84], byteorder="little"),
            "uuid2": UUID(self.data[84:100], byteorder="little"),
            "placed_on_type": PlacedOn(self.data[100]),
            "placed_on": PlacedOn(self.data[100]).parse_transaction(self.data[101:]),
        }
    