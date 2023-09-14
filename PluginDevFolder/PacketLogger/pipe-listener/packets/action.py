from enum import IntEnum

class Action(IntEnum):
    Drop = 0
    SendReliablePacket = 1
    SendUnreliablePacket = 2
    SendMessageToConnection = 3
    ReceiveMessagesOnPollGroup = 4
    ServerReceivePacket = 5
    ClientReceivePacket = 6
