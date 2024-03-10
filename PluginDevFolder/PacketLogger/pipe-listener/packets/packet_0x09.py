import enum
from packets.packet import Packet
from packets.construct_utils import UuidBE
from construct import Array, Byte, Enum, Int16ub, Int32ub, PascalString, Struct, this

class Gender(enum.IntEnum):
    Male = 0
    Female = 1

class CustomizationOption(enum.IntEnum):
    Face = 0
    Hair = 1
    FacialHair = 2
    Torso = 3
    Gloves = 4
    Shoes = 5
    Pants = 6
    Hat = 7
    Backpack = 8


packet_0x09 = Struct(
    "name" / PascalString(Int16ub, "utf8"),
    "version" / Int32ub, # Not sure, always 2
    "gender" / Enum(Byte, Gender),
    "customization_options_length" / Byte,
    "customization_options_uuids" / Array(this.customization_options_length, UuidBE),
    "customization_options_palette_indeces" / Array(this.customization_options_length, Int32ub),
)

class Packet_0x09(Packet):
    """Character Info"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x09.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x09.build(self.struct)