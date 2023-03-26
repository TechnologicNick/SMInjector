#pragma once

#include <Windows.h>
#include <type_traits>

#include "steam.h"
#include "logger.h"

#include <console.h>
using Console::Color;

constexpr uint64_t offset_HandleNetworkMessages = 0x44B560;

struct VolvoStructure
{
    void* m_functions[0xF];
};

using fGetNetworkingSocketInterface = std::add_pointer< uint64_t(VolvoStructure***) >::type;
using fReceiveMessagesOnPollGroup = std::add_pointer< int(void*, HSteamNetPollGroup, SteamNetworkingMessage_t**, int) >::type;
using fSendMessageToConnection = std::add_pointer< EResult(void*, HSteamNetConnection, const void*, uint32, int, int64*) >::type;

fReceiveMessagesOnPollGroup o_Steam_ReceiveMessagesOnPollGroup = nullptr;
fSendMessageToConnection o_Steam_SendMessageToConnection = nullptr;

namespace PacketLogger::Hooks {

    int hook_Steam_ReceiveMessagesOnPollGroup(void* self, HSteamNetPollGroup hPollGroup, SteamNetworkingMessage_t** ppOutMessages, int nMaxMessages) {
        int numMessages = o_Steam_ReceiveMessagesOnPollGroup(self, hPollGroup, ppOutMessages, nMaxMessages);
		
        SteamNetworkingMessage_t** outMsg = ppOutMessages;
        for (int i = 0; i < numMessages; i++) {
            SteamNetworkingMessage_t* message = outMsg[i];
            PacketLogger::Logger::LogInboundPacket(message);
        }

        return numMessages;
    }

    int hook_Steam_SendMessageToConnection(void* self, HSteamNetConnection hConn, const void* pData, uint32 cbData, int nSendFlags, int64* pOutMessageNumber) {
		PacketLogger::Logger::LogOutboundPacket(hConn, pData, cbData, nSendFlags, pOutMessageNumber);
        return o_Steam_SendMessageToConnection(self, hConn, pData, cbData, nSendFlags, pOutMessageNumber);
    }

    VolvoStructure** GetVolvoStructure() {
        const PBYTE pBaseAddress = PBYTE(GetModuleHandle(NULL));
        const fGetNetworkingSocketInterface pfnGetNetworkingSocketInterface = fGetNetworkingSocketInterface(pBaseAddress + offset_HandleNetworkMessages);

        VolvoStructure** ptr = nullptr;
        void* funcPtr = nullptr;

        pfnGetNetworkingSocketInterface(&ptr);

        return ptr;
    }

    bool InstallHooks() {
        Console::log(Color::Aqua, "Installing hooks...");

        VolvoStructure** ptr = GetVolvoStructure();
        o_Steam_ReceiveMessagesOnPollGroup = (fReceiveMessagesOnPollGroup)(*ptr)->m_functions[14];
		o_Steam_SendMessageToConnection = (fSendMessageToConnection)(*ptr)->m_functions[11];

		LPVOID pAddress = (LPVOID)&(*ptr)->m_functions[0];
        SIZE_T dwSize = sizeof(pAddress) * 14;
        DWORD oldProtect = 0;
        VirtualProtect(pAddress, dwSize, PAGE_READWRITE, &oldProtect);
        (*ptr)->m_functions[14] = &hook_Steam_ReceiveMessagesOnPollGroup;
		(*ptr)->m_functions[11] = &hook_Steam_SendMessageToConnection;
        VirtualProtect(pAddress, dwSize, oldProtect, NULL);

        Console::log(Color::Aqua, "Hooks installed!");
        return true;
    }

    bool UninstallHooks() {
        VolvoStructure** ptr = GetVolvoStructure();

        LPVOID pAddress = (LPVOID) & (*ptr)->m_functions[0];
        SIZE_T dwSize = sizeof(pAddress) * 14;
        DWORD oldProtect = 0;
        VirtualProtect(pAddress, dwSize, PAGE_READWRITE, &oldProtect);
        (*ptr)->m_functions[14] = &o_Steam_ReceiveMessagesOnPollGroup;
		(*ptr)->m_functions[11] = &o_Steam_SendMessageToConnection;
        VirtualProtect(pAddress, dwSize, oldProtect, NULL);

        Console::log(Color::Aqua, "Hooks uninstalled!");
        return true;
    }
}
