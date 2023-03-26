from packets.packet import Packet
from packets.bitfield import Bitfield

class Packet_0x1E(Packet):
    def __init__(self, id: int, data: bytes, hidden=False):
        super().__init__(id, data, hidden)

    def parse_packet(self):
        hexdump = " ".join(hex(letter)[2:].ljust(2, "0") for letter in self.data)
        keys = Bitfield(self.data[5:7], byteorder="little")
        return (hexdump, {
            "tick": int.from_bytes(self.data[1:5], byteorder="big"),
            "movement": {
                "all": str(keys.get_all_bits()),
                # TODO: Fix bit indices
                "jump": keys.get_bit(0),
                "crouch": keys.get_bit(1),
                "wasd": keys.get_bit(2),
                "sprint": keys.get_bit(3),
                "direction": keys.get_int_from_bits([13, 14, 15]), # 0 = right, increases by 1 every 45 degrees counter-clockwise
            },
            "yaw": self.data[7],
            "pitch": self.data[8],
        })
    