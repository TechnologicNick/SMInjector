def hexdump(data: bytes):
    return " ".join(hex(letter)[2:].zfill(2) for letter in data)