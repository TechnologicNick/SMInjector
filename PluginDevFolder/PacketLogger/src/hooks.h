#pragma once

#include <Windows.h>
#include <type_traits>

#pragma warning(push)
#pragma warning(disable : 4996)
#include <sdk/steam/steam_api.h>
#include <sdk/steam/steam_gameserver.h>
#pragma warning(pop)

#include <console.h>
using Console::Color;

constexpr uint64_t offset_HandleNetworkMessages = 0x44B560;

struct VolvoStructure
{
    void* m_functions[0xF];
};

using fGetNetworkingSocketInterface = std::add_pointer< uint64_t(VolvoStructure***) >::type;
using fReceiveMessagesOnPollGroup = std::add_pointer< int(void*, void*, SteamNetworkingMessage_t**, int) >::type;

fReceiveMessagesOnPollGroup o_Steam_ReceiveMessagesOnPollGroup = nullptr;

namespace PacketLogger::Hooks {

    int hook_Steam_ReceiveMessagesOnPollGroup(void* self, void* poll_group, SteamNetworkingMessage_t** out_msg, int msg_max) {
        int numMessages = o_Steam_ReceiveMessagesOnPollGroup(self, poll_group, out_msg, msg_max);
        SteamNetworkingMessage_t* outMsg = *out_msg;
        for (int i = 0; i < numMessages; i++) {
            SteamNetworkingMessage_t* message = &outMsg[i];
            unsigned int size = message->GetSize();

            Console::log(Color::LightPurple, "------------");
            Console::log(Color::LightPurple, " Size: %u", size);
            if (size > 0) {
                Console::log(Color::LightPurple, " PacketID: %u", PBYTE(message->GetData())[0]);
            }
        }

        return numMessages;
    }

    fReceiveMessagesOnPollGroup* GetReceiveMessagesOnPollGroupPtr() {
        const PBYTE pBaseAddress = PBYTE(GetModuleHandle(NULL));
        const fGetNetworkingSocketInterface pfnGetNetworkingSocketInterface = fGetNetworkingSocketInterface(pBaseAddress + offset_HandleNetworkMessages);

        VolvoStructure** ptr = nullptr;
        void* funcPtr = nullptr;

        pfnGetNetworkingSocketInterface(&ptr);

        return (fReceiveMessagesOnPollGroup*)&(*ptr)->m_functions[14];
    }

    bool InstallHooks() {
        Console::log(Color::Aqua, "Installing hooks...");

        fReceiveMessagesOnPollGroup* funcPtr = GetReceiveMessagesOnPollGroupPtr();
        o_Steam_ReceiveMessagesOnPollGroup = *funcPtr;

        DWORD oldProtect = 0;
        VirtualProtect(funcPtr, 8, PAGE_READWRITE, &oldProtect);
        *funcPtr = &hook_Steam_ReceiveMessagesOnPollGroup;
        VirtualProtect(funcPtr, 8, oldProtect, NULL);

        Console::log(Color::Aqua, "Hooks installed!");
        return true;
    }

    bool UninstallHooks() {
        fReceiveMessagesOnPollGroup* funcPtr = GetReceiveMessagesOnPollGroupPtr();

        DWORD oldProtect = 0;
        VirtualProtect(funcPtr, 8, PAGE_READWRITE, &oldProtect);
        *funcPtr = o_Steam_ReceiveMessagesOnPollGroup;
        VirtualProtect(funcPtr, 8, oldProtect, NULL);

        Console::log(Color::Aqua, "Hooks uninstalled!");
        return true;
    }
}
