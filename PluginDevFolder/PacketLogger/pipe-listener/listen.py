import time
from construct import Byte, Enum, GreedyBytes, Hex, Int32ul, Int64ul, Prefixed, PrefixedArray, Struct
import win32pipe, win32file, pywintypes
from packets.hexdump import hexdump
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
                # quit = True

PacketHeader = Struct(
    "action" / Enum(Byte, Action),
    "direction" / Enum(Byte, Direction),
    "return_address" / Hex(Int64ul),
    "data" / Prefixed(Int32ul, GreedyBytes),
)

def process_packet(handle: int, data: bytes):
    header = PacketHeader.parse(data)
    action = Action(int(header.action))
    direction = Direction(int(header.direction))

    response_packets = []

    if action in [Action.SendReliablePacket, Action.SendUnreliablePacket, Action.ServerReceivePacket, Action.ClientReceivePacket]:
        packet = registry.get_packet(header.data[0], header.data[1:])
        parsed_packet = packet.parse_packet()
        
        if not packet.hidden:
            dir = direction.name.ljust(8)
            id_hex = "0x" + hex(packet.id)[2:].zfill(2)
            id_dec = packet.id
            ret_addr = hex(header.return_address)[2:].zfill(16)
            size = len(header.data[1:])

            print(f"\033c{dir} packet {id_hex} ({id_dec}) from {ret_addr}: (size={size}) {parsed_packet}")
        
        packet.modify_packet(direction)

        built_packets = packet.build_packet()
        if not isinstance(built_packets, list):
            built_packets = [built_packets]

        for built_packet in built_packets:
            header.data = packet.id.to_bytes(1) + built_packet
            response_packets.append(PacketHeader.build(header))

    if action in [Action.SendReliablePacket, Action.SendUnreliablePacket, Action.ServerReceivePacket, Action.ClientReceivePacket]:
        send_response(handle, response_packets)

PipeResponse = PrefixedArray(Byte, GreedyBytes)

def send_response(handle: int, response_packets: list[bytes]):
    # Prepend the length of the array as one byte, then concatenate all the packets
    data = PipeResponse.build(response_packets)

    # print(f"Sending response: {hexdump(data)}")

    (result, bytes_written) = win32file.WriteFile(handle, data)

if __name__ == "__main__":
    pipe_client()
