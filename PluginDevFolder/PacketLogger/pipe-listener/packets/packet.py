from construct import setGlobalPrintFullStrings
from packets.direction import Direction

setGlobalPrintFullStrings(True)

class Packet:
    def __init__(self, id: int, data: bytes, hidden=False):
        self.id = id
        self.data = data
        self.hidden = hidden

    def parse_packet(self):
        return self.data
    
    def modify_packet(self, direction: Direction):
        return
    
    def build_packet(self) -> bytes | list[bytes]:
        return self.data
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, doc='{self.__class__.__doc__}')"
