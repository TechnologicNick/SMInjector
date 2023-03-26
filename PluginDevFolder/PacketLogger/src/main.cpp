#define _SM_LIBRARY_BUILD_PLUGIN
#define _SM_PLUGIN_NAME PacketLogger

#include <sm_lib.h>
#include <console.h>
using Console::Color;

#pragma comment(lib, "sdk/steam_api64.lib")

#include "hooks.h"

LIB_RESULT PluginLoad() {
	Console::log(Color::Aqua, "Loading...");
	
	if (!PacketLogger::Hooks::InstallHooks()) {
		Console::log(Color::Red, "Failed to install hooks");
		return PLUGIN_ERROR;
	}

	return PLUGIN_SUCCESSFULL;
}

LIB_RESULT PluginUnload() {
	Console::log(Color::Aqua, "Unloading...");
	return PLUGIN_SUCCESSFULL;
}
