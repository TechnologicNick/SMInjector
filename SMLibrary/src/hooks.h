#pragma once

#include <stdio.h>
#include "../include/gamehook.h"

#include "../include/console.h"
using Console::Color;

#include "../include/Event/ProcessStartEvent.hpp"

namespace Hooks {
	typedef DWORD (*pEntry)();

	using p_get_wide_winmain_command_line = std::add_pointer<decltype(_get_wide_winmain_command_line)>::type;

	GameHook* pHookAllocConsole;
	GameHook* pHookProcessStart;

	BOOL Hook_ReturnTrue() {
		return true;
	}

	wchar_t* __CRTDECL Hook_ProcessStart() {
		using namespace SMLibrary::Event;

		Console::log(Color::Aqua, "Process started!");

		GetEventBus<ProcessStartEvent>()->Emit({});

		return ((p_get_wide_winmain_command_line)*pHookProcessStart)();
	}

	bool InstallHooks() {
		Console::log(Color::Aqua, "Installing hooks...");

		// The target function has no prologue, so we must skip past the instructions that write to registers used by the trampoline function.
		pHookProcessStart = GameHooks::InjectFromName("ucrtbase.dll", "_get_wide_winmain_command_line", +14, Hook_ProcessStart, 6);

		if (!pHookProcessStart) {
			Console::log(Color::LightRed, "Failed to install hook for ProcessStart");
			return false;
		}

		Console::log(Color::Aqua, "Hooks installed!");
		return true;
	}
}
