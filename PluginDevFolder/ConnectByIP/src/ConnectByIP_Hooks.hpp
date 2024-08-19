#pragma once

#include <Windows.h>
#include <type_traits>
#include <iostream>
#include <gamehook.h>

#include "steam.h"
#include <sdk/sm/ScrapMechanic.hpp>

#include <console.h>
using Console::Color;

constexpr uint64_t offset_SteamNetworkClient_ConnectP2P = 0x448910;

namespace ConnectByIP::Hooks {

    SteamNetworkingIPAddr addr = { 0 };
    bool useIP = false;

    GameHook* gh_SteamNetworkClient_ConnectP2P;
    GameHook* gh_SteamAPI_RunCallbacks;

    using f_SteamNetworkingClient_ConnectP2P = std::add_pointer< void(void*, uint64_t*, std::string*) >::type;
    using f_ISteamNetworkingSockets_ConnectP2P = std::add_pointer< HSteamNetConnection(ISteamNetworkingSockets*, const SteamNetworkingIdentity&, int, int, const SteamNetworkingConfigValue_t*) >::type;
    using f_SteamAPI_RunCallbacks = std::add_pointer< void() >::type;

    f_ISteamNetworkingSockets_ConnectP2P o_ISteamNetworkingSockets_ConnectP2P = nullptr;

    HSteamNetConnection Hook_ISteamNetworkingSockets_ConnectP2P(ISteamNetworkingSockets* self, const SteamNetworkingIdentity& identityRemote, int nRemoteVirtualPort, int nOptions, const SteamNetworkingConfigValue_t* pOptions) {
        Console::log(Color::LightPurple, "Hook_ISteamNetworkingSockets_ConnectP2P, self = %p, identityRemote = %llu, nRemoteVirtualPort = %d, nOptions = %d", self, identityRemote.GetSteamID64(), nRemoteVirtualPort, nOptions);
        
        if (ConnectByIP::Hooks::useIP) {
			ConnectByIP::Hooks::useIP = false;
            char ip[256];
            addr.ToString(ip, sizeof(ip), true);

			Console::log(Color::LightPurple, "Connectign to IP address: %s", ip);
			return self->ConnectByIPAddress(ConnectByIP::Hooks::addr, nOptions, pOptions);
		}

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

    bool ParseConnectionString(const std::string& connectionString, SteamNetworkingIPAddr& addr) {
        const size_t pos = connectionString.find("://");
		std::string protocol = connectionString.substr(0, pos);
        if (protocol != "ip") {
            Console::log(Color::Red, "Invalid protocol: '%s'. Only 'ip' is supported.", protocol.c_str());
            return false;
        }

        const std::string ip = connectionString.substr(pos + 3);

		addr.Clear();
        if (!addr.ParseString(ip.c_str())) {
            Console::log(Color::Red, "Failed to parse IP address: '%s'", ip.c_str());
        }

        if (addr.m_port == 0) {
			addr.m_port = 38799;
		}

		return true;
	}

    void TransitionToPlayState() {
        if ((*SM::g_contraption)->m_uGameStateIndex != SM::GameState_MenuState) {
            Console::log(Color::LightPurple, "Not in main menu, ignoring join request");
            return;
        }

        Console::log(Color::LightPurple, "Transitioning to play state...");

        (*SM::g_contraption)->m_pGameStartupParams.m_ullConnectSteamId = -1; // Anything other than 0 to prevent the game from crashing

        // If the following are not set, the `!sFile.empty() && !sClass.empty()` assertion fails
        (*SM::g_contraption)->m_pGameStartupParams.m_bListenServer = false; // Required to fix `Invalid game mode`
        (*SM::g_contraption)->m_pGameStartupParams.m_sPassphraseUuid.clear(); // If this is left out you get `Timed out attempting to connect (5003)` after 10 seconds for every other attempt to connect
        (*SM::g_contraption)->m_pGameStartupParams.m_gameInfo.m_eGameMode = 0xFF;

        void* playState = &((*SM::g_contraption)->m_pGameStates[(*SM::g_contraption)->m_uGameStateIndex]);

        constexpr uint64_t offset_m_uTargetGameState = 0x118;
        uint64_t p_m_uTargetGameState = *(uint64_t*)playState + offset_m_uTargetGameState;

        *(int*)p_m_uTargetGameState = SM::GameState_PlayState;
    }

    void Hook_SteamAPI_RunCallbacks() {
		((f_SteamAPI_RunCallbacks)*gh_SteamAPI_RunCallbacks)();

        if (ConnectByIP::Pipes::hPipe == INVALID_HANDLE_VALUE) {
            ConnectByIP::Pipes::InitPipe();
		}

        std::string connectionString;
        if (ConnectByIP::Pipes::ReadConnectionString(connectionString)) {
			Console::log(Color::LightPurple, "Received message from pipe: %s", connectionString.c_str());
			if (ParseConnectionString(connectionString, addr)) {
                ConnectByIP::Hooks::useIP = true;
				TransitionToPlayState();
			}
		}
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

        gh_SteamAPI_RunCallbacks = GameHooks::InjectFromName("steam_api64.dll", "SteamAPI_RunCallbacks", Hook_SteamAPI_RunCallbacks, 6);
        if (!gh_SteamAPI_RunCallbacks) {
			Console::log(Color::Red, "Failed to install hook for 'SteamAPI_RunCallbacks'");
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
