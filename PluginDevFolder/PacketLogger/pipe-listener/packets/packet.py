class Packet:
    def __init__(self, id: int, data: bytes, hidden=False):
        self.id = id
        self.data = data
        self.hidden = hidden

    def parse_packet(self):
        return self.data
    
    def modify_packet(self):
        return
    
    def build_packet(self) -> bytes | list[bytes]:
        return self.data
