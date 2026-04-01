#define _SM_LIBRARY_BUILD_PLUGIN
#define _SM_PLUGIN_NAME Scraptifine

#include <sm_lib.h>
#include <console.h>
using Console::Color;

#include "hooks.h"
#include "pipes.h"

LIB_RESULT PluginLoad() {
	Console::log(Color::Aqua, "Loading...");

	if (!Scraptifine::Pipes::StartPipeServer()) {
		Console::log(Color::Red, "Failed to initialize Scraptifine pipe server");
		return PLUGIN_ERROR;
	}

	if (!Scraptifine::Hooks::InstallHooks()) {
		Console::log(Color::Red, "Failed to install hooks");
		Scraptifine::Pipes::StopPipeServer();
		return PLUGIN_ERROR;
	}

	return PLUGIN_SUCCESSFULL;
}

LIB_RESULT PluginUnload() {
	Console::log(Color::Aqua, "Unloading...");
	Scraptifine::Pipes::StopPipeServer();
	Scraptifine::Hooks::UninstallHooks();
	return PLUGIN_SUCCESSFULL;
}
