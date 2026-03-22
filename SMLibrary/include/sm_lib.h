/*
 * Created by HardCoded 2021 (c)
 * 
 * To build a custom plugin add this before you include this file
 *   #define _SM_LIBRARY_BUILD_PLUGIN
 *   #define _SM_PLUGIN_NAME PluginName
 * 
 * 
 * Contributors:
 *     TechnologicNick          (https://github.com/TechnologicNick)
 * 
 * https://github.com/Kariaro/SMInjector
 * 
 */

#include "stdafx.h"

typedef int LIB_RESULT;
typedef LIB_RESULT (*LIB_CALLBACK)();

#ifndef _SM_PLUGIN_NAME
#   error _SM_PLUGIN_NAME was undefined
#endif

#define _LIB_PLUGIN_NAME_STR__(X) #X
#define _LIB_PLUGIN_NAME_STR_(X) _LIB_PLUGIN_NAME_STR__(X)
#define _LIB_PLUGIN_NAME_STR "" _LIB_PLUGIN_NAME_STR_(_SM_PLUGIN_NAME) ""

#ifdef _SM_LIBRARY_BUILD_PLUGIN
#include "sdk/sm/Types.hpp"
#include <Windows.h>
#include "Event/ProcessStartEvent.hpp"

extern LIB_RESULT PluginLoad();
extern LIB_RESULT PluginUnload();

BOOL WINAPI DllMain(HMODULE hModule, DWORD fdwReason, LPVOID lpReserved) {

	switch (fdwReason) {
	case DLL_PROCESS_ATTACH:
		SMLibrary::Event::GetEventBus<SMLibrary::Event::ProcessStartEvent>()->RegisterHandler([](const SMLibrary::Event::ProcessStartEvent&) {
			PluginLoad();
		});
		break;

	case DLL_PROCESS_DETACH:
		break;

	case DLL_THREAD_ATTACH:
		break;

	case DLL_THREAD_DETACH:
		break;
	}

	return TRUE;
}
#endif
