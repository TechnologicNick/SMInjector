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

                process_packet(handle, data)
                
        except pywintypes.error as e:
            if e.args[0] == 2:
                print("no pipe, trying again in a sec")
                time.sleep(1)
            elif e.args[0] == 109:
                print("broken pipe, bye bye")
                quit = True

def process_packet(handle: int, data: bytes):
    action = Action(data[0])
    direction = Direction(data[1])
    size = int.from_bytes(data[2:6], byteorder="little")

    # print(f"{action.name} {direction.name} {size}: {data}")

    response_packets = []

    if action == Action.SendReliablePacket or action == Action.SendUnreliablePacket or action == Action.ReceivePacket:
        # response_packets.append(data)
        packet = registry.get_packet(data[6], data[7:])
        if not packet.hidden:
            # hexdump = " ".join(hex(letter)[2:].zfill(2) for letter in data[2:])
            print(f"{direction.name.ljust(8)}\t packet {hex(data[6]).zfill(2)} ({data[6]}): (size={len(data[7:])}) {packet.parse_packet()}")
        
        packet.modify_packet(direction)

        built_packets = packet.build_packet()
        if not isinstance(built_packets, list):
            built_packets = [built_packets]

        for built_packet in built_packets:
            payload = bytes([packet.id]) + built_packet
            payload = bytes([action.value, direction.value]) + len(payload).to_bytes(4, byteorder="little") + payload
            response_packets.append(payload)



    # if action == Action.SendMessageToConnection or action == Action.ReceiveMessagesOnPollGroup:
    #     packet = registry.get_packet(data[6], data[7:])
    #     if not packet.hidden:
    #         # hexdump = " ".join(hex(letter)[2:].zfill(2) for letter in data[2:])
    #         print(f"{direction.name.ljust(8)}\t packet {hex(data[6]).zfill(2)} ({data[6]}): (size={len(data[7:])}) {packet.parse_packet()}")

    if action == Action.SendReliablePacket or action == Action.SendUnreliablePacket or action == Action.ReceivePacket:
        send_response(handle, response_packets)

def send_response(handle: int, response_packets: list[bytes]):
    # Prepend the length of the array as one byte, then concatenate all the packets
    data = bytes([len(response_packets)]) + b"".join(response_packets)

    # print(f"Sending response: {data}")

    (result, bytes_written) = win32file.WriteFile(handle, data)
    # (result, bytes_written) = win32file.WriteFile(handle, b"\x00")


if __name__ == "__main__":
    pipe_client()
