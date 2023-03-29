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
