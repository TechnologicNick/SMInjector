#pragma once

#include <cstdint>
#include <memory>

namespace PacketLogger {

    enum Action : uint8_t {
        Drop = 0,
        SendReliablePacket = 1,
        SendUnreliablePacket = 2,
	};

    enum Direction : uint8_t {
        Outbound = 0,
        Inbound = 1,
    };

#pragma pack(push, 1)
    struct PacketHeader {
        Action action;
        Direction direction;
        uint32_t size;
    };
#pragma pack(pop)

    class Packet {
    public:
        char* buffer;
        uint32_t size;

        Packet(const PacketHeader& header, const char* pData) {
            this->size = sizeof(PacketHeader) + header.size;
            this->buffer = new char[this->size];
            memcpy_s(this->buffer, this->size, &header, sizeof(PacketHeader));
            memcpy(this->buffer + sizeof(PacketHeader), pData, header.size);
        }

        const char* GetData() const {
            return this->buffer + sizeof(PacketHeader);
        }

        const PacketHeader* GetHeader() const {
            return reinterpret_cast<PacketHeader*>(this->buffer);
        }

        static void DeletePacket(const Packet& packet) {
			delete[] packet.buffer;
		}
    };
}
