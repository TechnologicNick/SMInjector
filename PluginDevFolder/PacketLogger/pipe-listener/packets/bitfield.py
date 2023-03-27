class Bitfield:
    def __init__(self, input: bytes | int, byteorder = "big"):
        if isinstance(input, int):
            input = bytes([input])

        self.bitfield = int.from_bytes(input, byteorder=byteorder)
        self.len = len(input)
    
    def get_bit(self, bit: int):
        return (self.bitfield >> bit) & 1
    
    def get_all_bits(self):
        return [(bit, self.get_bit(bit)) for bit in range(self.len * 8 - 1, -1, -1)]
    
    def get_int_from_bits(self, bits: list):
        return sum([self.get_bit(bits[i]) * 2 ** i for i in range(len(bits))])
    
    def __str__(self):
        return bin(self.bitfield)[2:].zfill(16)
