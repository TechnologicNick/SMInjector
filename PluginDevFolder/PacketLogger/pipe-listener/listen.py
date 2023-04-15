import time
import win32pipe, win32file, pywintypes
from packets.registry import PacketRegistry
from packets.direction import Direction
from packets.action import Action

pipeName = "\\\\.\\pipe\\scrapmechanic"

registry = PacketRegistry()

def pipe_client():
    print("pipe client")
    quit = False

    while not quit:
        try:
            handle = win32file.CreateFile(
                pipeName,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
            if res == 0:
                print(f"SetNamedPipeHandleState return code: {res}")
            while True:
                (result, data) = win32file.ReadFile(handle, 0x80000)

                process_packet(data)
                
        except pywintypes.error as e:
            if e.args[0] == 2:
                print("no pipe, trying again in a sec")
                time.sleep(1)
            elif e.args[0] == 109:
                print("broken pipe, bye bye")
                quit = True

def process_packet(data: bytes):
    action = Action(data[0])
    direction = Direction(data[1])
    size = int.from_bytes(data[2:6], byteorder="little")

    print(f"{action.name} {direction.name} {size}")

    if action == Action.SendMessageToConnection or action == Action.ReceiveMessagesOnPollGroup:
        packet = registry.get_packet(data[6], data[7:])
        if not packet.hidden:
            # hexdump = " ".join(hex(letter)[2:].zfill(2) for letter in data[2:])
            print(f"{direction.name.ljust(8)}\t packet {hex(data[1]).zfill(2)} ({data[1]}): (size={len(data)-2}) {packet.parse_packet()}")


if __name__ == "__main__":
    pipe_client()
