#pragma once

#include <Windows.h>
#include "packets.h"
#include "steam.h"

namespace PacketLogger::Logger {
	void LogInboundPacket(SteamNetworkingMessage_t& message) {
        unsigned int size = message.GetSize();

        Console::log(Color::LightPurple, "------------ Inbound");
        Console::log(Color::LightPurple, " Size: %u", size);
		if (size > 0 && message.GetData() != nullptr) {
            Console::log(Color::LightPurple, " PacketID: %u", PBYTE(message.GetData())[0]);
        }
	}
	
    void LogOutboundPacket(HSteamNetConnection& hConn, const void*& pData, uint32& cbData, int& nSendFlags, int64*& pOutMessageNumber) {
		Console::log(Color::LightBlue, "------------ Outbound");
		Console::log(Color::LightBlue, " Size: %u", cbData);
		if (cbData > 0 && pData != nullptr) {
			Console::log(Color::LightBlue, " PacketID: %u", PBYTE(pData)[0]);
		}
    }
}