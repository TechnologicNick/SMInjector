import enum
from packets.packet import Packet
from packets.construct_utils import PaddingUntilAligned, RepeatUntilEOF, Uuid, UuidBE
from packets.packet_0x18 import NetObjType
from packets.hexdump import hexdump
from construct import Adapter, Aligned, Array, BitsInteger, Bitwise, Byte, Bytes, Bytewise, Computed, Enum, Flag, Float16b, Float32b, FocusedSeq, GreedyBytes, Hex, If, Int16sb, Int16ub, Int32sb, Int32ub, Int64ub, Optional, Padding, Pass, Prefixed, PrefixedArray, Probe, Rebuild, RestreamData, Select, Struct, Switch, Tunnel, len_, this

class AxisAdapter(Adapter):
    def _decode(self, obj, context, path):
        return obj - 4

    def _encode(self, obj, context, path):
        return obj + 4

CreateRigidBody = Bytewise(Switch(this.controller_type, {
    1: Struct(
        "world_id" / Int16sb,
        "rotation" / Struct(
            "w" / Float32b,
            "z" / Float32b,
            "y" / Float32b,
            "x" / Float32b,
        ),
        "position" / Struct(
            "x" / Float32b,
            "y" / Float32b,
            "z" / Float32b,
        ),
    ),
    2: Struct(
        "world_id" / Int16sb,
        "rotation" / Struct(
            "x" / Float32b,
            "y" / Float32b,
            "z" / Float32b,
            "w" / Float32b,
        ),
        "position" / Struct(
            "x" / Float32b,
            "y" / Float32b,
            "z" / Float32b,
        ),
        "velocity" / Struct(
            "x" / Float32b,
            "y" / Float32b,
            "z" / Float32b,
        ),
        "angular_velocity" / Struct(
            "x" / Float32b,
            "y" / Float32b,
            "z" / Float32b,
        ),
    ),
}, default=Pass))

class ChildShapeControllerType(enum.IntEnum):
    Block = 31
    Part = 32

CreateChildShape = Struct(
    "shape_type" / Enum(Computed(this._.controller_type), ChildShapeControllerType),
)

class JointControllerType(enum.IntEnum):
    Bearing = 2
    Spring = 3
    SurvivalSpring = 4
    Piston = 28 # Also SurvivalPiston
    GenericRotational = 41

CreateJoint = Struct(
    "joint_type" / Enum(Computed(this._.controller_type), JointControllerType),
)

CreateContainer = Bytewise(Struct(
    "size" / Int16ub,
    "stack_size" / Int16ub,
    "items" / Array(this.size, Struct(
        "uuid" / Uuid,
        "instance_id" / Int32ub,
        "quantity" / Int16ub,
    )),
    "filter" / PrefixedArray(Int16ub, UuidBE),
))

CreateHarvestable = Bytewise(Struct(
    "world_id" / Int16sb,
    "uuid" / Int16ub,
    "initial_position" / Struct(
        "x" / Float32b,
        "y" / Float32b,
        "z" / Float32b,
    ),
    "initial_rotation" / Struct(
        "w" / Float32b,
        "z" / Float32b,
        "y" / Float32b,
        "x" / Float32b,
    ),
    "idk1" / Float16b,
    "idk2" / Float16b,
))

CreateCharacter = Bytewise(Struct(
    "steam_id_64" / Int64ub,
    "position" / Struct(
        "z" / Float32b,
        "y" / Float32b,
        "x" / Float32b,
    ),
    "world_id" / Int16sb,
    "yaw" / Float32b,
    "pitch" / Float32b,
    "character_uuid" / Uuid,
))

CreateLift = Bytewise(Struct(
    "steam_id_64" / Int64ub,
    "world_id" / Int16sb,
    "pos" / Struct(
        "x" / Int32sb,
        "y" / Int32sb,
        "z" / Int32sb,
    ),
    "level" / Int32sb,
))

CreateTool = Bytewise(Struct(
    "uuid" / Uuid,
))

UpdateRigidBody = Select(
    # 1 - Static
    Bytewise(Struct(
        "unknown" / Byte,
        "unknown2" / Int32sb,
    )),
    # 2 - Dynamic
    Bytewise(Struct(
        "unknown" / Byte,
        "revision" / Byte,
    )),
)

UpdateChildShape = Bytewise(Struct(
    "uuid" / Int16ub,
    "parent_body_id" / Int32ub,
    "pos" / Struct(
        "x" / Int16sb,
        "y" / Int16sb,
        "z" / Int16sb,
    ),
    "color" / Struct(
        "a" / Hex(Byte),
        "b" / Hex(Byte),
        "g" / Hex(Byte),
        "r" / Hex(Byte),
    ),
    "data" / Select(
        # Blocks
        Struct(
            "bounds" / Struct(
                "x" / Int16sb,
                "y" / Int16sb,
                "z" / Int16sb,
            ),
        ),
        # Parts
        Struct(
            "axis" / Bitwise(Struct(
                "z_axis" / AxisAdapter(BitsInteger(4)),
                "x_axis" / AxisAdapter(BitsInteger(4)),
            )),
        ),
    ),
))

UpdateJoint = Bytewise(Struct(
    "uuid" / Int16ub,
    "id_shape_a" / Int32sb,
    "id_shape_b" / Int32sb,
    "pos_a" / Struct(
        "x" / Int32sb,
        "y" / Int32sb,
        "z" / Int32sb,
    ),
    "pos_b" / Struct(
        "x" / Int32sb,
        "y" / Int32sb,
        "z" / Int32sb,
    ),
    "axis" / Bitwise(Struct(
        "z_axis_b" / AxisAdapter(BitsInteger(4)),
        "z_axis_a" / AxisAdapter(BitsInteger(4)),
        "x_axis_b" / AxisAdapter(BitsInteger(4)),
        "x_axis_a" / AxisAdapter(BitsInteger(4)),
    )),
    "color" / Struct(
        "a" / Hex(Byte),
        "b" / Hex(Byte),
        "g" / Hex(Byte),
        "r" / Hex(Byte),
    ),
))

UpdateContainer = Struct(
    "slot_changes" / Bytewise(PrefixedArray(Int16ub, Struct(
        "uuid" / Uuid,
        "instance_id" / Int32ub,
        "quantity" / Int16ub,
        "slot" / Int16ub,
    ))),
    "has_filters" / Flag,
    "filters" / If(this.has_filters, FocusedSeq("filters",
        "filter_count" / Bytewise(Rebuild(Int16ub, len_(this.filters))),
        PaddingUntilAligned(8),
        "filters" / Bytewise(Array(this.filter_count, UuidBE)),
    )),
)

UpdateHarvestable = Bytewise(Struct(
    "color" / Struct(
        "r" / Hex(Byte),
        "g" / Hex(Byte),
        "b" / Hex(Byte),
        "a" / Hex(Byte),
    ),
    "seated_character_id" / Optional(Int32ub), # Only present if the harvestable has a kinematic seat component
))


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

UpdateLift = Bytewise(Struct(
    "level" / Int32ub,
))

UpdateTool = Bytewise(Struct(
    "owner_player_id" / Int32ub,
))

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
            NetObjType.RigidBody.name: CreateRigidBody,
            NetObjType.ChildShape.name: CreateChildShape,
            NetObjType.Joint.name: CreateJoint,
            NetObjType.Container.name: CreateContainer,
            NetObjType.Harvestable.name: CreateHarvestable,
            NetObjType.Character.name: CreateCharacter,
            NetObjType.Lift.name: CreateLift,
            NetObjType.Tool.name: CreateTool,
        }, default=Pass),

        UpdateType.P.name: Bytes(0), # The game doesn't read anything for this update type

        UpdateType.Update.name: Switch(this.net_obj_type, {
            NetObjType.RigidBody.name: UpdateRigidBody,
            NetObjType.ChildShape.name: UpdateChildShape,
            NetObjType.Joint.name: UpdateJoint,
            NetObjType.Container.name: UpdateContainer,
            NetObjType.Harvestable.name: UpdateHarvestable,
            NetObjType.Character.name: UpdateCharacter,
            NetObjType.Lift.name: UpdateLift,
            NetObjType.Tool.name: UpdateTool,
        }, default=Pass),

        UpdateType.Remove.name: Switch(this.net_obj_type, {
            NetObjType.RigidBody.name: Struct(),
            NetObjType.ChildShape.name: Struct(),
            NetObjType.Joint.name: Struct(),
            NetObjType.Container.name: Struct(),
            NetObjType.Harvestable.name: Struct(),
            NetObjType.Character.name: Struct(),
            NetObjType.Lift.name: Struct(),
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
                    accumulator = ""
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
