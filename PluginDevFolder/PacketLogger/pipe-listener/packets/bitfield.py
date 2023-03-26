class Bitfield:
    def __init__(self, bytes: bytes, byteorder = "big"):
        self.bitfield = int.from_bytes(bytes, byteorder=byteorder)
        self.len = len(bytes)
    
    def get_bit(self, bit: int):
        return (self.bitfield >> bit) & 1
    
    def get_all_bits(self):
        return [self.get_bit(bit) for bit in range(self.len * 8)]
    
    def get_int_from_bits(self, bits: list):
        return sum([self.get_bit(bits[i]) * 2 ** i for i in range(len(bits))])
    
    def __str__(self):
        return bin(self.bitfield)[2:].zfill(16)
