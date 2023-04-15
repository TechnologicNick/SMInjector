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

	void LogInboundPacket(SteamNetworkingMessage_t* message) {
		if (message->m_cbSize <= 0 || message->m_pData == nullptr) {
			return;
		}

		PacketHeader header = {
			.action = Action::ReceiveMessagesOnPollGroup,
			.direction = Direction::Inbound,
			.size = uint32_t(message->m_cbSize)
		};

		Packet packet(header, (const char*)message->m_pData);

		SendPacket(packet);

		Packet::DeletePacket(packet);
	}
	
    void LogOutboundPacket(HSteamNetConnection& hConn, const void*& pData, uint32& cbData, int& nSendFlags, int64*& pOutMessageNumber) {
		if (cbData == 0 || pData == nullptr) {
			return;
		}

		PacketHeader header = {
			.action = Action::SendMessageToConnection,
			.direction = Direction::Outbound,
			.size = cbData
		};

		Packet packet(header, (const char*)pData);

		SendPacket(packet);

		Packet::DeletePacket(packet);
    }

	std::vector<Packet> LogPacket(const Packet& packet) {
		std::vector<Packet> packets;

		// If we failed to send the packet, don't modify it
		if (!SendPacket(packet)) {
			packets.push_back(packet);
		}

		return packets;
	}

	void Breakpoint() {

	}
}