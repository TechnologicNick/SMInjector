#define _SM_LIBRARY_BUILD_PLUGIN
#define _SM_PLUGIN_NAME NetworkingHook

#include <sm_lib.h>
#include <console.h>
#include <Windows.h>

#include "hooks.h"

using Console::Color;

LIB_RESULT PluginLoad() {
	Console::log(Color::Aqua, "Loading this plugin!");
	Console::log(Color::Aqua, "Hello World!");

	// TODO: Hook SteamAPI_RegisterCallback and log all function addresses of CCallbackImpl

	HMODULE hModule = GetModuleHandleA("steam_api64.dll");
	if (!hModule) {
		return PLUGIN_ERROR;
	}

	{
		// This function starts with a lot of relative instructions, so we inject at the near jump's destination
		DWORD64 pRegisterCallback = (DWORD64)GetProcAddress(hModule, "SteamAPI_RegisterCallback");
		
		// Select the near jump instruction
		DWORD64 jmpInstruction = pRegisterCallback + 33;
		
		// Dereference the destination
		DWORD64 jmpDestination = jmpInstruction + *(INT32*)(jmpInstruction + 1);

		// Skip past the int 3 instructions at the destination
		DWORD64 movInstruction = jmpDestination + 5;

		hck_SteamAPI_RegisterCallback = GameHooks::Inject((void*)movInstruction, &Hooks::hook_SteamAPI_RegisterCallback, 5);
	}

	if (!hck_SteamAPI_RegisterCallback) {
		Console::log(Color::Red, "Failed to inject 'SteamAPI_RegisterCallback'");
		return false;
	}

	return PLUGIN_SUCCESSFULL;
}

LIB_RESULT PluginUnload() {
	Console::log(Color::Aqua, "Unloading this plugin!");
	return PLUGIN_SUCCESSFULL;
}
