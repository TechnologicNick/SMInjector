#pragma once

#include <Windows.h>
#include "packets.h"
#include "steam.h"

namespace PacketLogger::Logger {
	void LogPacket(SteamNetworkingMessage_t& message) {
        unsigned int size = message.GetSize();

        Console::log(Color::LightPurple, "------------");
        Console::log(Color::LightPurple, " Size: %u", size);
        if (size > 0) {
            Console::log(Color::LightPurple, " PacketID: %u", PBYTE(message.GetData())[0]);
        }
	}
}