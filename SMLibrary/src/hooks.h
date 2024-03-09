#pragma once

#include <stdio.h>
#include "../include/gamehook.h"

#include "../include/console.h"
using Console::Color;

#include "../include/Event/ProcessStartEvent.hpp"
#include "../include/Event/SteamInitializedEvent.hpp"

namespace Hooks {
	typedef DWORD (*pEntry)();

	using p_get_wide_winmain_command_line = std::add_pointer<decltype(_get_wide_winmain_command_line)>::type;
	using fRegisterClassW = std::add_pointer<decltype(RegisterClassW)>::type;

	GameHook* pHookAllocConsole;
	p_get_wide_winmain_command_line original_get_wide_winmain_command_line;
	fRegisterClassW original_RegisterClassW;

	BOOL Hook_ReturnTrue() {
		return true;
	}

	wchar_t* __CRTDECL Hook_ProcessStart() {
		using namespace SMLibrary::Event;

		Console::log(Color::Aqua, "Process started!");

		GetEventBus<ProcessStartEvent>()->Emit({});

		return original_get_wide_winmain_command_line();
	}

	ATOM WINAPI Hook_RegisterClassW(CONST WNDCLASSW* lpWndClass) {
		using namespace SMLibrary::Event;
		
		GetEventBus<SteamInitializedEvent>()->Emit({});

		Console::log(Color::Aqua, "Registering class %s", lpWndClass->lpszClassName);

		return original_RegisterClassW(lpWndClass);
	}

	bool InstallHooks() {
		Console::log(Color::Aqua, "Installing hooks...");

		original_get_wide_winmain_command_line = (p_get_wide_winmain_command_line)GameHooks::InjectFromImportAddressTable(
			GetModuleHandle(NULL),
			"api-ms-win-crt-runtime-l1-1-0.dll",
			"_get_wide_winmain_command_line",
			(FARPROC)Hook_ProcessStart
		);

		if (!original_get_wide_winmain_command_line) {
			Console::log(Color::LightRed, "Unable to find process start function");
			return false;
		}
		Console::log(Color::Aqua, "Found process start function at %p", original_get_wide_winmain_command_line);

		original_RegisterClassW = (fRegisterClassW)GameHooks::InjectFromImportAddressTable(
			GetModuleHandle(NULL),
			"user32.dll",
			"RegisterClassW",
			(FARPROC)Hook_RegisterClassW
		);

		if (!original_RegisterClassW) {
			Console::log(Color::LightRed, "Unable to find RegisterClassW");
			return false;
		}
		Console::log(Color::Aqua, "Found RegisterClassW at %p", original_RegisterClassW);

		Console::log(Color::Aqua, "Hooks installed!");
		return true;
	}
}
