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
    COLLECT_TO_SLOT = 5
    MOVE_INVALID = 6
    MOVE_DRAG = 7
    MOVE_SHIFT_CLICK = 8
    
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
        elif self == Action.COLLECT_TO_SLOT:
            return (1 + ItemStack.size() + 1, {
                "item": ItemStack.parse(data[1:]),
                "unknown": data[1 + ItemStack.size()],
            })
        elif self == Action.MOVE_INVALID:
            return (1 + ItemStack.size() + 1, {
                "from": ItemStack.parse(data[1:]),
                "unknown": data[1 + ItemStack.size()],
            })
        elif self == Action.MOVE_DRAG:
            return (1 + ItemStack.size() + ItemStack.size() + 1, {
                "from": ItemStack.parse(data[1:]),
                "to": ItemStack.parse(data[1 + ItemStack.size():]),
                "unknown": data[1 + ItemStack.size() + ItemStack.size()],
            })
        elif self == Action.MOVE_SHIFT_CLICK:
            return (1 + 2 + 4 + 4, {
                "slot_from": int.from_bytes(data[1:3], byteorder="big"),
                "container_from": int.from_bytes(data[3:7], byteorder="big"),
                "container_to": int.from_bytes(data[7:11], byteorder="big"),
            })


class Packet_0x20(Packet):
    """Change Hotbar Item"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        decompressed: bytes = decompress(self.data, uncompressed_size=100)
        # print("Decompressed:", hexdump(decompressed))

        transaction_count = int.from_bytes(decompressed[0:1], byteorder="big")
        transactions = []
        ptr = 1
        for i in range(transaction_count):
            transaction_struct = decompressed[ptr:]

            action = Action(transaction_struct[0])
            (size, data) = action.parse_transaction(transaction_struct)

            transactions.append({
                "action": action,
                "data": data,
            })

            ptr += size
            

        return {
            "transaction_count": transaction_count,
            "transactions": transactions,
        }
    