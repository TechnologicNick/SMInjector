#include <stdio.h>
#include "../include/gamehook.h"

#include "../include/console.h"
using Console::Color;

// INIT_CONSOLE
typedef void (*pinit_console)(void*, void*);
GameHook *hck_init_console;

// =============

namespace Hooks {
	GameHook* pHookAllocConsole;

	BOOL Hook_ReturnTrue() {
		return true;
	}

	void hook_init_console(void* a, void* b) {
		((pinit_console)*hck_init_console)(a, b);
		PostConsoleInjections();
		return;
	}
}
