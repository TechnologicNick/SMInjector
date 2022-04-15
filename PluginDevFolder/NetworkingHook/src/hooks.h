#pragma once
#include <stdio.h>
#include <gamehook.h>
#pragma warning(push)
#pragma warning(disable : 4996 26812)
#define _CRT_SECURE_NO_WARNINGS
#include <steam_api.h>
#pragma warning(pop)

#include <console.h>
using Console::Color;

typedef void (*pSteamAPI_RegisterCallback)(class CCallbackBase* pCallback, int iCallback);
GameHook* hck_SteamAPI_RegisterCallback;

typedef int (*pReceiveMessagesOnPollGroup)(HSteamNetPollGroup hPollGroup, SteamNetworkingMessage_t** ppOutMessages, int nMaxMessages);
GameHook* hck_ReceiveMessagesOnPollGroup;

typedef void** (*pFindOrCreateUserInterface_SteamNetworkingSockets)(void** ptr);
GameHook* hck_FindOrCreateUserInterface_SteamNetworkingSockets;

namespace Hooks {

	void hook_SteamAPI_RegisterCallback(class CCallbackBase* pCallback, int iCallback) {
		Console::log(Color::Aqua, "SteamAPI_RegisterCallback: pCallback=[%p] iCallback=[%d]", pCallback, iCallback);

		((pSteamAPI_RegisterCallback)*hck_SteamAPI_RegisterCallback)(pCallback, iCallback);
	}

	void* hook_FindOrCreateUserInterface_SteamNetworkingSockets(void** ptr) {
		Console::log(Color::LightPurple, "FindOrCreateUserInterface_SteamNetworkingSockets: ptr=[%p]", ptr);

		void** toReturn = ((pFindOrCreateUserInterface_SteamNetworkingSockets)*hck_FindOrCreateUserInterface_SteamNetworkingSockets)(ptr);

		Console::log(Color::LightPurple, "FindOrCreateUserInterface_SteamNetworkingSockets: toReturn=[%p]", toReturn);

		return toReturn;
	}

	int hook_ReceiveMessagesOnPollGroup(HSteamNetPollGroup hPollGroup, SteamNetworkingMessage_t** ppOutMessages, int nMaxMessages) {
		Console::log(Color::LightPurple, "ReceiveMessagesOnPollGroup: hPollGroup=[%p] ppOutMessages=[%p] nMaxMessages[%d]", hPollGroup, ppOutMessages, nMaxMessages);



		return ((pReceiveMessagesOnPollGroup)*hck_ReceiveMessagesOnPollGroup)(hPollGroup, ppOutMessages, nMaxMessages);
	}
}
