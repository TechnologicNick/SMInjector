#pragma once

#include <Windows.h>
#include <type_traits>
#include <gamehook.h>
#include <vector>
#include <intrin.h>

#include "steam.h"
#include "logger.h"

#include <console.h>
using Console::Color;

constexpr uint64_t offset_HandleNetworkMessages = 0x44B560;
constexpr uint64_t offset_NetworkSendInterface_SendReliablePacket = 0x90c8b0;
constexpr uint64_t offset_NetworkSendInterface_SendUnreliablePacket = 0x90d010;
constexpr uint64_t offset_SteamNetworkServer_ReceivePacket = 0x8df070;
constexpr uint64_t offset_SteamNetworkClient_ReceivePacket = 0x4351e0;

struct VolvoStructure
{
    void* m_functions[0xF];
};

struct SteamNetworkServer
{
    char m_pad_0x0000[0x120]; //0x0000
    char* m_pDecompressedDataBuffer; //0x0120
};

using fGetNetworkingSocketInterface = std::add_pointer< uint64_t(VolvoStructure***) >::type;
using fReceiveMessagesOnPollGroup = std::add_pointer< int(void*, HSteamNetPollGroup, SteamNetworkingMessage_t**, int) >::type;
using fSendMessageToConnection = std::add_pointer< EResult(void*, HSteamNetConnection, const void*, uint32, int, int64*) >::type;
using fSendReliablePacket = std::add_pointer< void(const void* self, const void* param_2, const char* data, uint32 size, const uint32 param_5, const uint8 param_6, int* pOutCompressedSize) >::type;
using fSendUnreliablePacket = std::add_pointer< void(const void* self, const void* param_2, const char* data, uint32 size, const void* param_5, int* pOutCompressedSize) >::type;
using fServerReceivePacket = std::add_pointer< void(SteamNetworkServer* self, const void* player, const void* param_3, const uint64 iDecompressedSize) >::type;
using fClientReceivePacket = std::add_pointer< int(const void* self, const void* player, const char* data, const uint64 iDecompressedSize, const char param_5) >::type;

fReceiveMessagesOnPollGroup o_Steam_ReceiveMessagesOnPollGroup = nullptr;
fSendMessageToConnection o_Steam_SendMessageToConnection = nullptr;

GameHook* hck_SendReliablePacket;
GameHook* hck_SendUnreliablePacket;
GameHook* hck_ServerReceivePacket;
GameHook* hck_ClientReceivePacket;

namespace PacketLogger::Hooks {

    int hook_Steam_ReceiveMessagesOnPollGroup(void* self, HSteamNetPollGroup hPollGroup, SteamNetworkingMessage_t** ppOutMessages, int nMaxMessages) {
        int numMessages = o_Steam_ReceiveMessagesOnPollGroup(self, hPollGroup, ppOutMessages, nMaxMessages);
		
        SteamNetworkingMessage_t** outMsg = ppOutMessages;
        for (int i = 0; i < numMessages; i++) {
            SteamNetworkingMessage_t* message = outMsg[i];
            PacketLogger::Logger::LogInboundPacket(message, _ReturnAddress());
        }

        return numMessages;
    }

    int hook_Steam_SendMessageToConnection(void* self, HSteamNetConnection hConn, const void* pData, uint32 cbData, int nSendFlags, int64* pOutMessageNumber) {
		PacketLogger::Logger::LogOutboundPacket(hConn, pData, cbData, nSendFlags, pOutMessageNumber, _ReturnAddress());
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

    void hook_SendReliablePacket(const void* self, const void* param_2, const char* data, uint32 size, const uint32 param_5, const uint8 param_6, int* pOutCompressedSize) {
        // Console::log(Color::Aqua, "SendReliablePacket called! packet id = %u, size = %u", ((uint8*)data)[0], size);

        PacketHeader header = {
            .action = Action::SendReliablePacket,
            .direction = Direction::Outbound,
            .return_address = uint64_t(_ReturnAddress()),
            .size = size,
        };

        Packet originalPacket(header, data);

        std::vector<Packet> packets = Logger::SendAndReceivePacket(originalPacket);
        for (const Packet& packet : packets) {
            if (packet.GetHeader()->action != Action::SendReliablePacket) {
                continue;
            }

			((fSendReliablePacket)*hck_SendReliablePacket)(self, param_2, packet.GetData(), packet.GetHeader()->size, param_5, param_6, pOutCompressedSize);
            
            Packet::DeletePacket(packet);
		}

        // ((fSendReliablePacket)*hck_SendReliablePacket)(self, param_2, data, size, param_5, param_6, pOutCompressedSize);
    }

    void hook_SendUnreliablePacket(const void* self, const void* param_2, const char* data, uint32 size, const void* param_5, int* pOutCompressedSize) {
        // Console::log(Color::Aqua, "SendUnreliablePacket called! packet id = %u, size = %u", ((uint8*)data)[0], size);

        PacketHeader header = {
			.action = Action::SendUnreliablePacket,
			.direction = Direction::Outbound,
            .return_address = uint64_t(_ReturnAddress()),
			.size = size,
		};

        Packet originalPacket(header, data);

        std::vector<Packet> packets = Logger::SendAndReceivePacket(originalPacket);
        for (const Packet& packet : packets) {
            if (packet.GetHeader()->action != Action::SendUnreliablePacket) {
                continue;
            }

            std::string packetData(packet.GetData(), packet.GetHeader()->size);

            ((fSendUnreliablePacket)*hck_SendUnreliablePacket)(self, param_2, packet.GetData(), packet.GetHeader()->size, param_5, pOutCompressedSize);

            Packet::DeletePacket(packet);
        }

        // ((fSendUnreliablePacket)*hck_SendUnreliablePacket)(self, param_2, data, size, param_5, pOutCompressedSize);
    }

    void hook_ServerReceivePacket(SteamNetworkServer* self, const void* player, const void* param_3, const uint64 iDecompressedSize) {
        //Console::log(Color::Aqua, "ReceivePacket called! %p %p %p %llu", self, player, param_3, iDecompressedSize);

        PacketHeader header = {
            .action = Action::ServerReceivePacket,
            .direction = Direction::Inbound,
            .return_address = uint64_t(_ReturnAddress()),
            .size = (uint32)iDecompressedSize,
        };

        Packet originalPacket(header, self->m_pDecompressedDataBuffer);

        std::vector<Packet> packets = Logger::SendAndReceivePacket(originalPacket);
        for (const Packet& packet : packets) {
            if (packet.GetHeader()->action != Action::ServerReceivePacket) {
                continue;
            }

            std::string packetData(packet.GetData(), packet.GetHeader()->size);

            memcpy_s(self->m_pDecompressedDataBuffer, 0x80000, packet.GetData(), packet.GetHeader()->size);

            ((fServerReceivePacket)*hck_ServerReceivePacket)(self, player, param_3, packet.GetHeader()->size);

            Packet::DeletePacket(packet);
        }
    }

int hook_ClientReceivePacket(const void* self, const void* player, const char* data, const uint64 iDecompressedSize, const char param_5) {
		//Console::log(Color::Aqua, "SteamNetworkClient::ReceivePacket called! %p %p %p %llu %u", self, player, data, iDecompressedSize, param_5);

        if (iDecompressedSize > 0x80000) {
            Console::log(Color::Red, "Packet size is too big! %llu", iDecompressedSize);
            return ((fClientReceivePacket)*hck_ClientReceivePacket)(self, player, data, iDecompressedSize, param_5);
		} 

		PacketHeader header = {
			.action = Action::ClientReceivePacket,
			.direction = Direction::Inbound,
            .return_address = uint64_t(_ReturnAddress()),
			.size = (uint32)iDecompressedSize,
		};

		Packet originalPacket(header, data);

		std::vector<Packet> packets = Logger::SendAndReceivePacket(originalPacket);
		for (const Packet& packet : packets) {
			if (packet.GetHeader()->action != Action::ClientReceivePacket) {
				continue;
			}

			std::string packetData(packet.GetData(), packet.GetHeader()->size);

			int iReadBytes = ((fClientReceivePacket)*hck_ClientReceivePacket)(self, player, packet.GetData(), packet.GetHeader()->size, param_5);

			Packet::DeletePacket(packet);
		}

		return (int)iDecompressedSize;
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

        const PBYTE pBaseAddress = PBYTE(GetModuleHandle(NULL));

        hck_SendReliablePacket = GameHooks::Inject(pBaseAddress + offset_NetworkSendInterface_SendReliablePacket, hook_SendReliablePacket, 5);
        hck_SendUnreliablePacket = GameHooks::Inject(pBaseAddress + offset_NetworkSendInterface_SendUnreliablePacket, hook_SendUnreliablePacket, 5);
        hck_ServerReceivePacket = GameHooks::Inject(pBaseAddress + offset_SteamNetworkServer_ReceivePacket, hook_ServerReceivePacket, 6);
        hck_ClientReceivePacket = GameHooks::Inject(pBaseAddress + offset_SteamNetworkClient_ReceivePacket, hook_ClientReceivePacket, 5);

        if (!hck_SendReliablePacket) {
			Console::log(Color::Red, "Failed to inject 'SendReliablePacket'!");
			return false;
		}

        if (!hck_SendUnreliablePacket) {
            Console::log(Color::Red, "Failed to inject 'SendUnreliablePacket'");
            return false;
        }

        if (!hck_ServerReceivePacket) {
			Console::log(Color::Red, "Failed to inject 'ReceivePacket'");
			return false;
		}

        if (!hck_ClientReceivePacket) {
            Console::log(Color::Red, "Failed to inject 'ReceivePacket'");
            return false;
        }

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
