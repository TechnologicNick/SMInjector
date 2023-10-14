#pragma once

#include <Windows.h>
#include "packets.h"
#include "steam.h"
#include <system_error>
#include <vector>

LPCTSTR pipeName = TEXT("\\\\.\\pipe\\scrapmechanic");

namespace PacketLogger::Logger {
	HANDLE hPipe = INVALID_HANDLE_VALUE;

	bool InitPipe() {
		if (hPipe != INVALID_HANDLE_VALUE) {
			CloseHandle(hPipe);
		}
		
        hPipe = CreateNamedPipe(
            pipeName,
            PIPE_ACCESS_DUPLEX,
            PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
            1,
            0x80000,
			0x80000,
            0,
            NULL
        );
		
        if (hPipe == INVALID_HANDLE_VALUE) {
			Console::log(Color::LightRed, "Failed to create named pipe: %s", std::system_category().message(GetLastError()).c_str());
            return false;
        }

        return true;
	}

	bool SendPacket(const Packet& packet) {
		DWORD dwWritten;
		if (!WriteFile(hPipe, packet.buffer, packet.size, &dwWritten, NULL)) {
			DWORD error = GetLastError();
			if (error != ERROR_PIPE_LISTENING) {
				Console::log(Color::LightRed, "Failed to write to pipe: %s (%d)", std::system_category().message(error).c_str(), error);
			}
			if (error == ERROR_NO_DATA) {
				InitPipe();
			}
			return false;
		}

		return true;
	}

	bool ReceivePacket(std::vector<Packet>& packets) {
		constexpr DWORD nNumberOfBytesToRead = 1 + sizeof(PacketHeader) + 0x80000;
		char buffer[nNumberOfBytesToRead];

		DWORD dwRead;
		if (!ReadFile(hPipe, buffer, nNumberOfBytesToRead, &dwRead, NULL)) {
			DWORD error = GetLastError();
			if (error != ERROR_PIPE_LISTENING) {
				Console::log(Color::LightRed, "Failed to read from pipe: %s (%d)", std::system_category().message(error).c_str(), error);
			}
			if (error == ERROR_NO_DATA) {
				InitPipe();
			}
			return false;
		}

		if (dwRead == 0) {
			return false;
		}

		uint8_t packetCount = buffer[0];
		char* ptr = buffer + 1;
		for (uint8_t i = 0; i < packetCount; i++) {
			PacketHeader* header = reinterpret_cast<PacketHeader*>(ptr);
			char* data = new char[header->size];
			memcpy(data, ptr + sizeof(PacketHeader), header->size);
			packets.emplace_back(*header, data);
			ptr += sizeof(PacketHeader) + header->size;
		}

		return true;
	}

	void LogInboundPacket(SteamNetworkingMessage_t* message, void* returnAddress) {
		if (message->m_cbSize <= 0 || message->m_pData == nullptr) {
			return;
		}

		PacketHeader header = {
			.action = Action::ReceiveMessagesOnConnection,
			.direction = Direction::Inbound,
			.return_address = uint64_t(returnAddress),
			.size = uint32_t(message->m_cbSize),
		};

		Packet packet(header, (const char*)message->m_pData);

		SendPacket(packet);

		Packet::DeletePacket(packet);
	}
	
    void LogOutboundPacket(HSteamNetConnection& hConn, const void*& pData, uint32& cbData, int& nSendFlags, int64*& pOutMessageNumber, void* returnAddress) {
		if (cbData == 0 || pData == nullptr) {
			return;
		}

		PacketHeader header = {
			.action = Action::SendMessageToConnection,
			.direction = Direction::Outbound,
			.return_address = uint64_t(returnAddress),
			.size = cbData,
		};

		Packet packet(header, (const char*)pData);

		SendPacket(packet);

		Packet::DeletePacket(packet);
    }

	std::vector<Packet> SendAndReceivePacket(const Packet& packet) {
		std::vector<Packet> packets;

		// If we failed to send the packet, don't modify it
		if (!SendPacket(packet)) {
			packets.push_back(packet);
			return packets;
		}

		ReceivePacket(packets);

		return packets;
	}

	void Breakpoint() {

	}
}