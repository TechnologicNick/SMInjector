import enum
from packets.packet import Packet
from packets.construct_utils import RepeatUntilEOF, Uuid
from packets.packet_0x18 import NetObjType
from construct import Aligned, BitsInteger, Bitwise, Byte, Bytes, Bytewise, Enum, Flag, GreedyBytes, Hex, If, Int16ub, Int32ub, Pass, Peek, Prefixed, Struct, Switch, this

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

packet_0x16 = Struct(
    "tick" / Int32ub,
    "updates" / RepeatUntilEOF(Struct(
        "special_bit" / Peek(Byte),
        "update_data" / Switch(this.special_bit & 0x80 == 0x80, {
            False: Prefixed(Int16ub, Bitwise(Aligned(8, Struct(
                "update_type" / Enum(BitsInteger(3), UpdateType),
                "net_obj_type" / Enum(BitsInteger(5), NetObjType),
                "unknown_create_byte" / If(this.update_type == UpdateType.Create.name, Bytewise(Byte)),
                "net_obj_id" / Bytewise(Int32ub),

                "data" / Switch(this.update_type, {
                    UpdateType.Create.name: Switch(this.net_obj_type, {
                        NetObjType.Lift.name: Struct(
                            "height" / Bytewise(Int32ub),
                        )
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
            ))), includelength=True),
            True: GreedyBytes, # TODO: Implement decompression
        }, default=GreedyBytes),
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
        # for update in self.struct.updates:
        #     if update.special_bit & 0x80 == 0x80:
        #         continue
        #     if update.update_data.update_type == UpdateType.Update.name and update.update_data.net_obj_type == NetObjType.Lift.name:
        #         update.update_data.data.height = 0x7fffffff
        pass
    
    def build_packet(self):
        # return self.data
        return packet_0x16.build(self.struct)
