#pragma once

#include <Windows.h>
#include <type_traits>
#include <gamehook.h>

#include "steam.h"
#include <sdk/sm/ScrapMechanic.hpp>

#include <console.h>
using Console::Color;

constexpr uint64_t offset_SteamNetworkClient_ConnectP2P = 0x448910;

namespace ConnectByIP::Hooks {

    GameHook* gh_SteamNetworkClient_ConnectP2P;

    using f_SteamNetworkingClient_ConnectP2P = std::add_pointer< void(void*, uint64_t*, std::string*) >::type;
    using f_ISteamNetworkingSockets_ConnectP2P = std::add_pointer< HSteamNetConnection(ISteamNetworkingSockets*, const SteamNetworkingIdentity&, int, int, const SteamNetworkingConfigValue_t*) >::type;

    f_ISteamNetworkingSockets_ConnectP2P o_ISteamNetworkingSockets_ConnectP2P = nullptr;

    HSteamNetConnection Hook_ISteamNetworkingSockets_ConnectP2P(ISteamNetworkingSockets* self, const SteamNetworkingIdentity& identityRemote, int nRemoteVirtualPort, int nOptions, const SteamNetworkingConfigValue_t* pOptions) {
        Console::log(Color::LightPurple, "Hook_ISteamNetworkingSockets_ConnectP2P, self = %p, identityRemote = %llu, nRemoteVirtualPort = %d, nOptions = %d", self, identityRemote.GetSteamID64(), nRemoteVirtualPort, nOptions);
        
        SteamNetworkingIPAddr addr = { 0 };
        addr.SetIPv6LocalHost(38799);

        self->ConnectByIPAddress(addr, nOptions, pOptions);

        return o_ISteamNetworkingSockets_ConnectP2P(self, identityRemote, nRemoteVirtualPort, nOptions, pOptions);
    }

    void Hook_SteamNetworkClient_ConnectP2P(void* self, uint64_t* pulHostUserId, std::string* sPassphrase) {
        Console::log(Color::LightPurple, "Hook_SteamNetworkClient_ConnectP2P, self = %p, ulHostUserId = %llu, sPassphrase = %s", self, *pulHostUserId, sPassphrase->c_str());
        
        if (!o_ISteamNetworkingSockets_ConnectP2P) {
            f_ISteamNetworkingSockets_ConnectP2P* ptr = (f_ISteamNetworkingSockets_ConnectP2P*)(*(uint64_t*)SteamNetworkingSockets() + 0x18);
            o_ISteamNetworkingSockets_ConnectP2P = *ptr;
            Console::log(Color::Aqua, "SteamNetworkingSockets()->ConnectP2P = %p", o_ISteamNetworkingSockets_ConnectP2P);

            DWORD oldProtect = 0;
            VirtualProtect(ptr, sizeof(ptr), PAGE_READWRITE, &oldProtect);
            *ptr = Hook_ISteamNetworkingSockets_ConnectP2P;
            VirtualProtect(ptr, sizeof(ptr), oldProtect, &oldProtect);
		}

        ((f_SteamNetworkingClient_ConnectP2P)*gh_SteamNetworkClient_ConnectP2P)(self, pulHostUserId, sPassphrase);
    }

    bool InstallHooks() {
        Console::log(Color::Aqua, "Installing hooks...");

        Console::log(Color::Aqua, "g_contraption = %p", SM::g_contraption);

        const PBYTE pBaseAddress = PBYTE(GetModuleHandle(NULL));
        gh_SteamNetworkClient_ConnectP2P = GameHooks::Inject(pBaseAddress + offset_SteamNetworkClient_ConnectP2P, Hook_SteamNetworkClient_ConnectP2P, 5);
        
        if (!gh_SteamNetworkClient_ConnectP2P) {
			Console::log(Color::Red, "Failed to install hook for 'SteamNetworkClient::ConnectP2P'");
			return false;
		}

        Console::log(Color::Aqua, "Hooks installed!");
        return true;
    }

    bool UninstallHooks() {
        Console::log(Color::Aqua, "Hooks uninstalled!");
        return true;
    }
}
