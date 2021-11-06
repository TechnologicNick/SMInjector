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

namespace Hooks {

	void hook_SteamAPI_RegisterCallback(class CCallbackBase* pCallback, int iCallback) {
		Console::log(Color::Aqua, "SteamAPI_RegisterCallback: pCallback=[%p] iCallback=[%d]", pCallback, iCallback);

		((pSteamAPI_RegisterCallback)*hck_SteamAPI_RegisterCallback)(pCallback, iCallback);
	}
}
