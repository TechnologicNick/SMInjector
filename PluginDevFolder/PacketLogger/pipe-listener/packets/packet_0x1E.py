from packets.packet import Packet
from packets.bitfield import Bitfield

class Packet_0x1E(Packet):
    def __init__(self, id: int, data: bytes, hidden=True):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        keys = Bitfield(self.data[5])
        direction = Bitfield(self.data[6])
        return {
            "tick": int.from_bytes(self.data[1:5], byteorder="big"),
            "keys": {
                "jump": keys.get_bit(0),
                "crouch": keys.get_bit(1),
                "wasd": keys.get_bit(2),
                "sprint": keys.get_bit(3),
            },
            "direction": direction.get_int_from_bits([7, 6, 5]), # 0 = right, increases by 1 every 45 degrees counter-clockwise
            "yaw": self.data[7],
            "pitch": self.data[8],
        }
    