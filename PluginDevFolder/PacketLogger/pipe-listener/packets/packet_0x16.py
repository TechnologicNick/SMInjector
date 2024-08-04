import enum
from packets.packet import Packet
from packets.construct_utils import RepeatUntilEOF, Uuid
from packets.packet_0x18 import NetObjType
from packets.hexdump import hexdump
from construct import Aligned, BitsInteger, Bitwise, Byte, Bytes, Bytewise, Enum, Flag, FocusedSeq, GreedyBytes, Hex, If, Int16ub, Int32ub, Padding, Pass, Prefixed, Struct, Switch, Tunnel, this

UpdateCharacter = Struct(
    "update_movement_states" / Flag,
    "update_color" / Flag,
    "update_selected_item" / Flag,
    "update_is_player" / Flag,

    "movement_states" / If(this.update_movement_states, Struct(
        "is_downed" / Flag,
        "is_swimming" / Flag,
        "is_diving" / Flag,
        "unknown" / Flag, # Possibly is_aiming or value from Tool:setMovementSlowDown
        "is_climbing" / Flag,
        "is_tumbling" / Flag,
    )),

    "color" / If(this.update_color, Bytewise(Struct(
        "r" / Hex(Byte),
        "g" / Hex(Byte),
        "b" / Hex(Byte),
        "a" / Hex(Byte),
    ))),

    "selected_item" / If(this.update_selected_item, Struct(
        "uuid" / Bytewise(Uuid),
        "instance_id" / Bytewise(Int32ub),
    )),

    "is_player" / If(this.update_is_player, Struct(
        "is_player" / Flag,
        "unit_id" / Bytewise(Int32ub),
    )),
)

class UpdateType(enum.IntEnum):
    Create = 1
    P = 2 # Sent when the body of a joint is updated. Only possible for joints.
    Update = 3
    Remove = 5

NetworkUpdate = Prefixed(Int16ub, Bitwise(Aligned(8, Struct(
    "update_type" / Enum(BitsInteger(3), UpdateType),
    "net_obj_type" / Enum(BitsInteger(5), NetObjType),
    "controller_type" / If(this.update_type == UpdateType.Create.name, Bytewise(Byte)),
    "net_obj_id" / Bytewise(Int32ub),

    "data" / Switch(this.update_type, {
        UpdateType.Create.name: Switch(this.net_obj_type, {
            NetObjType.Lift.name: Struct(
                "height" / Bytewise(Int32ub),
            ),
            NetObjType.Tool.name: Struct(
                "uuid" / Bytewise(Uuid),
            ),
        }, default=Pass),

        UpdateType.P.name: Bytes(0), # The game doesn't read anything for this update type

        UpdateType.Update.name: Switch(this.net_obj_type, {
            NetObjType.Character.name: UpdateCharacter,
            NetObjType.Lift.name: Struct(
                "height" / Bytewise(Int32ub),
            )
        }, default=Pass),

        UpdateType.Remove.name: Switch(this.net_obj_type, {
            NetObjType.Lift.name: Pass,
        }, default=Pass),
    }, default=Pass),

    "remainder" / Bytewise(GreedyBytes),
))), includelength=True)

class CompressedUpdate(Tunnel):
    """Decompresses a sequence of compressed network updates"""

    def __init__(self, subcon, print_data=False):
        super().__init__(subcon)
        self.print_data = print_data

    def _decode(self, data, context, path):
        output = b""

        index = 0

        prev_uncompressed_data = b""

        while index < len(data):
            special_bit = data[index] & 0x80

            if not special_bit:
                size = Int16ub.parse(data[index:index+2])
                prev_uncompressed_data = data[index:index+size]
                assert len(prev_uncompressed_data) == size, f"Expected {size} bytes, got {len(prev_uncompressed_data)} bytes: {hexdump(prev_uncompressed_data)}"

                if self.print_data:
                    print("uncompressed", hexdump(prev_uncompressed_data), NetworkUpdate.parse(prev_uncompressed_data))

                output += prev_uncompressed_data
                index += size
            else:
                u16ObjSize = len(prev_uncompressed_data) - 2
                assert u16ObjSize <= 0x3f
                uBitfieldSizeInBytes = (u16ObjSize + 8) >> 3
                assert uBitfieldSizeInBytes > 0 and uBitfieldSizeInBytes <= 8

                Bitfield = Bitwise(FocusedSeq("bitfield",
                    "special_bit" / Padding(1),
                    "bitfield" / Flag[uBitfieldSizeInBytes * 8 - 1],
                ))


                keep_bitfield = Bitfield.parse(data[index:index+uBitfieldSizeInBytes])

                # Seek to the next byte after the bitfield
                index += uBitfieldSizeInBytes

                reconstructed = list(prev_uncompressed_data[2:])

                # Iterate over the bitfield in reverse order. For each bit, if it is set,
                # keep the corresponding byte from the previous uncompressed data.
                # If it is not set, use the next byte from the compressed data and increment the index.
                for (byte_index, keep) in enumerate(keep_bitfield[::-1][:u16ObjSize]):
                    if not keep:
                        reconstructed[byte_index] = data[index]
                        index += 1

                # Prepend the size of the update to the reconstructed data
                reconstructed = prev_uncompressed_data[:2] + bytes(reconstructed)

                assert len(reconstructed) == len(prev_uncompressed_data), f"Expected {len(prev_uncompressed_data)} bytes, got {len(reconstructed)} bytes: {hexdump(reconstructed)}"

                if self.print_data:
                    # Print the differences between the previous uncompressed data and the reconstructed data
                    accumulator = hexdump(prev_uncompressed_data[:2]) + " "
                    for i in range(len(reconstructed)):
                        if reconstructed[i] != prev_uncompressed_data[i]:
                            accumulator += f"\033[91m{reconstructed[i]:02x}\033[0m "
                        else:
                            accumulator += f"{reconstructed[i]:02x} "

                    print("reconstructed", accumulator, NetworkUpdate.parse(reconstructed))

                prev_uncompressed_data = reconstructed

                output += reconstructed

        return output

    def _encode(self, data, context, path):
        return data

packet_0x16 = Struct(
    "tick" / Int32ub,
    "updates" / CompressedUpdate(RepeatUntilEOF(NetworkUpdate)),
)

class Packet_0x16(Packet):
    """Network Update"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        self.struct = packet_0x16.parse(self.data)
        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return packet_0x16.build(self.struct)
