#define _SM_LIBRARY_BUILD_PLUGIN
#define _SM_PLUGIN_NAME WorkshopTools

#include <sm_lib.h>
#include <console.h>
using Console::Color;

#include "hooks.h"

LIB_RESULT PluginLoad() {
	Console::log(Color::Aqua, "Starting plugin...");

	if (!WorkshopTools::Hooks::Install()) {
		return PLUGIN_ERROR;
	}

	return PLUGIN_SUCCESSFULL;
}

LIB_RESULT PluginUnload() {
	Console::log(Color::Aqua, "Unloading this plugin!");
	return PLUGIN_SUCCESSFULL;
}
