from typing import Literal

class UUID:
    def __init__(self, bytes, byteorder: Literal["little", "big"] = "big"):
        self.byteorder = byteorder
        self.bytes = byteorder == "big" and bytes or bytes[-1::-1]
    
    def __str__(self):
        return "-".join([
            self.bytes[0:4].hex(),
            self.bytes[4:6].hex(),
            self.bytes[6:8].hex(),
            self.bytes[8:10].hex(),
            self.bytes[10:16].hex(),
        ])
    
    def __repr__(self):
        return f"UUID('{self.__str__()}')"

class Vec3i:
    def __init__(self, bytes, byteorder: Literal["little", "big"] = "big", signed: bool = True):
        self.byteorder = byteorder
        self.bytes = byteorder == "big" and bytes or bytes[-1::-1]
        self.signed = signed
    
    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"
    
    def __repr__(self):
        return f"Vec3i{self.__str__()}"
    
    @property
    def z(self):
        return int.from_bytes(self.bytes[0:4], byteorder=self.byteorder, signed=self.signed)
    
    @property
    def y(self):
        return int.from_bytes(self.bytes[4:8], byteorder=self.byteorder, signed=self.signed)
    
    @property
    def x(self):
        return int.from_bytes(self.bytes[8:12], byteorder=self.byteorder, signed=self.signed)
