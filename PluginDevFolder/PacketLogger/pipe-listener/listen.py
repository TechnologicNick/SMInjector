import time
import win32pipe, win32file, pywintypes
from packets.registry import PacketRegistry
from packets.direction import Direction

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
                resp = win32file.ReadFile(handle, 0x80000)
                # print(f"message: {resp}")

                data = resp[1]
                direction = Direction(data[0]).name
                packet = registry.get_packet(data[1], data[2:])
                if not packet.hidden:
                    print(f"{direction.ljust(8)}\t packet {hex(data[1])}: {packet.parse_packet()}")

        except pywintypes.error as e:
            if e.args[0] == 2:
                print("no pipe, trying again in a sec")
                time.sleep(1)
            elif e.args[0] == 109:
                print("broken pipe, bye bye")
                quit = True

if __name__ == "__main__":
    pipe_client()
