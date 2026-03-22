from packets.construct_utils import Uuid
from construct import Enum, Float32b, GreedyBytes, HexDump, Int32ub, Struct, Switch, this
import enum

class UserdataTypeId(enum.IntEnum):
    Uuid = 10001
    Vec3 = 10003
    Quat = 10004
    Color = 10005
    RaycastResult = 10006 # Cannot be serialized at all
    LoadCellHandle = 10007 # Unknown
    Effect = 10008 # Cannot be serialized at all
    Shape = 10021
    Body = 10022
    Interactable = 10023
    Container = 10024
    Harvestable = 10025
    Network = 10026 # Cannot be serialized at all
    World = 10027
    Unit = 10028 # Cannot be deserialized on client, event and storage only
    Storage = 10029 # Cannot be serialized at all
    Player = 10030
    Character = 10031
    Joint = 10032
    AiState = 10033 # Cannot be serialized at all
    AreaTrigger = 10035 # Cannot be serialized at all
    Portal = 10036 # Cannot be sent to client, event and storage only
    PathNode = 10037 # Cannot be sent to client, event and storage only
    Lift = 10038
    ScriptableObject = 10039
    BuilderGuide = 10040 # Cannot be serialized at all
    CullSphereGroup = 10041 # Cannot be serialized at all
    VoxelTerrain = 10042 # Unknown
    Widget = 20001 # Unknown
    Tool = 20002
    GuiInterface = 20006 # Cannot be serialized at all
    BlueprintVisualization = 20007 # Cannot be serialized at all

LuaUserdata = Struct(
    "type_id" / Enum(Int32ub, UserdataTypeId),
    "data" / Switch(this.type_id, {
        "Uuid": Uuid,
        "Vec3": Struct(
            "x" / Float32b,
            "y" / Float32b,
            "z" / Float32b,
        ),
        "Quat": Struct(
            "x" / Float32b,
            "y" / Float32b,
            "z" / Float32b,
            "w" / Float32b,
        ),
        "Color": Struct(
            "r" / Float32b,
            "g" / Float32b,
            "b" / Float32b,
            "a" / Float32b,
        ),
        "Shape": Struct(
            "shape_id" / Int32ub,
        ),
        "Body": Struct(
            "body_id" / Int32ub,
        ),
        "Interactable": Struct(
            "interactable_id" / Int32ub,
        ),
        "Container": Struct(
            "container_id" / Int32ub,
        ),
        "Harvestable": Struct(
            "harvestable_id" / Int32ub,
        ),
        "World": Struct(
            "world_id" / Int32ub,
        ),
        "Unit": Struct(
            "unit_id" / Int32ub,
        ),
        "Player": Struct(
            "player_id" / Int32ub,
        ),
        "Character": Struct(
            "character_id" / Int32ub,
        ),
        "Joint": Struct(
            "joint_id" / Int32ub,
        ),
        "Portal": Struct(
            "portal_id" / Int32ub,
        ),
        "PathNode": Struct(
            "pathnode_id" / Int32ub,
        ),
        "Lift": Struct(
            "lift_id" / Int32ub,
        ),
        "ScriptableObject": Struct(
            "scriptableobject_id" / Int32ub,
        ),
        "Tool": Struct(
            "tool_id" / Int32ub,
        ),
    }, default=HexDump(GreedyBytes)),
)
