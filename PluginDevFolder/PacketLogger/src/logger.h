#pragma once

#include <Windows.h>
#include "packets.h"
#include "steam.h"
#include <system_error>

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

	void LogInboundPacket(SteamNetworkingMessage_t* message) {
		if (message->m_cbSize > 0 && message->m_pData != nullptr) {
			int bufferSize = 1 + message->m_cbSize;
			char* buffer = new char[bufferSize];
			buffer[0] = Direction::Inbound;
			memcpy(buffer + 1, message->m_pData, message->m_cbSize);

  		    DWORD dwWritten = 0;
		    if (!WriteFile(hPipe, buffer, bufferSize, &dwWritten, NULL)) {
                DWORD error = GetLastError();
				if (error != ERROR_PIPE_LISTENING) {
		    		Console::log(Color::LightRed, "Failed to write to pipe: %s (%d)", std::system_category().message(error).c_str(), error);
				}
				
				if (error == ERROR_NO_DATA) {
					InitPipe();
				}
		    }

			delete[] buffer;
        }
	}
	
    void LogOutboundPacket(HSteamNetConnection& hConn, const void*& pData, uint32& cbData, int& nSendFlags, int64*& pOutMessageNumber) {
		if (cbData > 0 && pData != nullptr) {
			uint32_t bufferSize = 1 + cbData;
			char* buffer = new char[bufferSize];
			buffer[0] = Direction::Outbound;
			memcpy(buffer + 1, pData, cbData);

			DWORD dwWritten;
			if (!WriteFile(hPipe, buffer, bufferSize, &dwWritten, NULL)) {
				DWORD error = GetLastError();
				if (error != ERROR_PIPE_LISTENING) {
					Console::log(Color::LightRed, "Failed to write to pipe: %s (%d)", std::system_category().message(error).c_str(), error);
				}

				if (error == ERROR_NO_DATA) {
					InitPipe();
				}
			}

			delete[] buffer;
		}
    }

	void Breakpoint() {

	}
}