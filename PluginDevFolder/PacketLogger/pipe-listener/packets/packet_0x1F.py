from packets.packet import Packet
from packets.types import UUID
from lz4.block import decompress

class Packet_0x1F(Packet):
    """Equipped Item Changed"""

    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        return {
            "character_id": int.from_bytes(self.data[0:4], byteorder="big"),
            "uuid": UUID(bytes=self.data[4:20], byteorder="little"),
            "tool_instance_id": int.from_bytes(self.data[20:24], byteorder="big"),
        }
    