#pragma once
#include "stdafx.h"
#include "gamehook.h"
#include "sigscan.h"

#ifdef _SM_LIBRARY_BUILD_PLUGIN
	#define GLOBAL _LIB_IMPORT extern
#else
	#define GLOBAL _LIB_EXPORT

	typedef void* (*pVoidPtrFunc)();

	#define HOOK_RETURN_VALUE(name) \
		GameHook* gamehook_##name##;												\
		void* callback_##name##() {													\
			##name## = ((pVoidPtrFunc)*gamehook_##name##)();						\
			Console::log(Color::Aqua, "[Globals] Set " #name " to %p", ##name##);	\
			return (##name##);														\
		}

	#define INJECT_SIGSCAN(scanner, name, signature, mask, offset, size) \
		{																										\
			DWORD64 addr = scanner.scan(signature, mask, offset);												\
			if (!addr) {																						\
				Console::log(Color::LightRed, "[Globals] Unable to find function for " #name " in memory");		\
				return false;																					\
			}																									\
																												\
			gamehook_##name## = GameHooks::Inject((void*)addr, &callback_##name##, size);						\
			if (!gamehook_##name##) {																			\
				Console::log(Color::LightRed, "[Globals] Failed to hook function for " #name);					\
				return false;																					\
			}																									\
			Console::log(Color::Aqua, "[Globals] Set " #name " to the return value of %p", gamehook_##name##);	\
		}

#endif



GLOBAL void* g_contraptionUserGeneratedContentManager;



#ifndef _SM_LIBRARY_BUILD_PLUGIN
namespace Globals {

	HOOK_RETURN_VALUE(g_contraptionUserGeneratedContentManager);

	bool Inject() {
		SignatureScanner sigScanner(L"ScrapMechanic.exe");
		if (!sigScanner.readMemory()) {
			Console::log(Color::LightRed, "Failed to read the memory of ScrapMechanic.exe");
			return false;
		}

		INJECT_SIGSCAN(sigScanner, g_contraptionUserGeneratedContentManager, "\x89\x54\x24\x10\x48\x89\x4C\x24\x08\x53\x48\x83\xEC\x70\xC7\x44\x24\x60\x81\x03\x00\x00\x48\x8D", "xxxxxxxxxxxxxxxxxxxxxxxx", 0, 9);

		return true;
	}
}
#endif
