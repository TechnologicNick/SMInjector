from packets.packet import Packet
from packets.hexdump import hexdump
from packets.construct_utils import RepeatUntilEOF, Uuid
from construct import Aligned, BitsInteger, Bitwise, Byte, Bytewise, Flag, GreedyBytes, Hex, If, Int16ub, Int32ub, Pass, Peek, Prefixed, Probe, Struct, Switch, this

CharacterNetworkUpdate = Struct(
    "update_movement_states" / Flag,
    "update_color" / Flag,
    "update_selected_item" / Flag,
    "update_is_player" / Flag,

    "movement_states" / If(this.update_movement_states, Struct(
            "is_downed" / Flag,
            "is_swimming" / Flag,
            "is_diving" / Flag,
            "unknown" / Flag,
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

packet_0x16 = Struct(
    "tick" / Int32ub,
    "updates" / RepeatUntilEOF(Struct(
        "special_bit" / Peek(Flag),
        "update_data" / Switch(this.special_bit, {
            False: Prefixed(Int16ub, Bitwise(Aligned(8, Struct(
                "update_type" / BitsInteger(3),
                "net_obj_type" / BitsInteger(5),
                "net_obj_id" / Bytewise(Int32ub),

                "update" / Switch(this.update_type, {
                    3: Switch(this.net_obj_type, {
                        6: CharacterNetworkUpdate,
                    }, default=Pass),
                }, default=Pass),

                "data" / Bytewise(GreedyBytes),
            ))), includelength=True),
            True: GreedyBytes,
        }),
    )),
)

class Packet_0x16(Packet):
    """Network Update"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        # print(hexdump(self.data))

        self.struct = packet_0x16.parse(self.data)

        return self.struct
    
    def modify_packet(self, direction):
        pass
    
    def build_packet(self):
        return self.data
        # return packet_0x15.build(self.struct)
