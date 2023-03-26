class Packet:
    def __init__(self, id, data, hidden=False):
        self.id = id
        self.data = data
        self.hidden = hidden

    def parse_packet(self):
        return self.data
