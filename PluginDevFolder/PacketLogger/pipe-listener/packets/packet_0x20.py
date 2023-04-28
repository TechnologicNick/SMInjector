from packets.packet import Packet
from packets.hexdump import hexdump
from packets.types import UUID
from lz4.block import decompress
from enum import IntEnum

class ItemStack:

    @staticmethod
    def parse(data: bytes):
        return {
            "uuid": UUID(data[0:16]),
            "tool_instance_id": int.from_bytes(data[16:20], byteorder="big"),
            "quantity": int.from_bytes(data[20:22], byteorder="big"),
            "slot": int.from_bytes(data[22:24], byteorder="big"),
            "container_id": int.from_bytes(data[24:28], byteorder="big"),
        }
    
    @staticmethod
    def size():
        return 28
    
class Action(IntEnum):
    SET_ITEM = 0
    SWAP = 1
    COLLECT = 2
    SPEND = 3 # Never seen this one
    COLLECT_TO_SLOT = 4 # Never seen this one
    COLLECT_TO_SLOT_OR_COLLECT = 5
    SPEND_FROM_SLOT = 6
    MOVE = 7
    MOVE_FROM_SLOT = 8
    MOVE_ALL = 9

    UNKNOWN = -1
    
    def parse_transaction(self, data: bytes):
        if self == Action.SET_ITEM:
            return (1 + ItemStack.size(), {
                "to": ItemStack.parse(data[1:]),
            })
        elif self == Action.SWAP:
            return (1 + ItemStack.size() + ItemStack.size(), {
                "from": ItemStack.parse(data[1:]),
                "to": ItemStack.parse(data[1 + ItemStack.size():]),
            })
        elif self == Action.COLLECT:
            return (1 + 16 + 4 + 2 + 4 + 1, {
                "uuid": UUID(data[1:17]),
                "tool_instance_id": int.from_bytes(data[17:21], byteorder="big"),
                "quantity": int.from_bytes(data[21:23], byteorder="big"),
                "container_id": int.from_bytes(data[23:27], byteorder="big"),
                "must_collect_all": data[27],
            })
        elif self == Action.COLLECT_TO_SLOT:
            return (1 + ItemStack.size() + 1, {
                "to": ItemStack.parse(data[1:]),
                "must_collect_all": data[1 + ItemStack.size()],
            })
        elif self == Action.COLLECT_TO_SLOT_OR_COLLECT:
            return (1 + ItemStack.size() + 1, {
                "to": ItemStack.parse(data[1:]),
                "must_collect_all": data[1 + ItemStack.size()],
            })
        elif self == Action.SPEND_FROM_SLOT:
            return (1 + ItemStack.size() + 1, {
                "from": ItemStack.parse(data[1:]),
                "unknown": data[1 + ItemStack.size()],
            })
        elif self == Action.MOVE:
            return (1 + ItemStack.size() + ItemStack.size() + 1, {
                "from": ItemStack.parse(data[1:]),
                "to": ItemStack.parse(data[1 + ItemStack.size():]),
                "unknown": data[1 + ItemStack.size() + ItemStack.size()],
            })
        elif self == Action.MOVE_FROM_SLOT:
            return (1 + 2 + 4 + 4, {
                "slot_from": int.from_bytes(data[1:3], byteorder="big"),
                "container_from": int.from_bytes(data[3:7], byteorder="big"),
                "container_to": int.from_bytes(data[7:11], byteorder="big"),
            })
        elif self == Action.MOVE_ALL:
            return (1 + 4 + 4, {
                "container_from": int.from_bytes(data[1:5], byteorder="big"),
                "container_to": int.from_bytes(data[5:9], byteorder="big"),
            })
        elif self == Action.UNKNOWN:
            return (1, {
                "action": data[0],
                "data": hexdump(data[1:]),
            })
        else:
            raise Exception(f"Unknown action: {self}")
    
    @classmethod
    def _missing_(self, value):
        return Action.UNKNOWN


class Packet_0x20(Packet):
    """Container Transaction"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        print("Decompressed:", hexdump(self.data))

        transaction_count = int.from_bytes(self.data[0:1], byteorder="big")
        transactions = []
        ptr = 1
        for i in range(transaction_count):
            transaction_struct = self.data[ptr:]

            action = Action(transaction_struct[0])
            (size, data) = action.parse_transaction(transaction_struct)

            transactions.append({
                "action": action,
                "data": data,
            })

            ptr += size

            # TODO: Reverse engineer the second transaction
            if i > 0:
                break
            

        return {
            "transaction_count": transaction_count,
            "transactions": transactions,
        }
    