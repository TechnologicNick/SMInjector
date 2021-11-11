#pragma once
#include <gamehook.h>
#include <sigscan.h>

#include <console.h>
using Console::Color;

namespace WorkshopTools::Hooks {
	
	struct ToolManager {
		void* base;
		const char** toollistFile;
		size_t unknown;
		size_t toollistFileLength;
	};



	typedef void (*pload_toolsetlist)(void*, const char**);
	GameHook* hck_load_toolsetlist;

	typedef void (*pload_toollist)(ToolManager*, const char**);
	GameHook* hck_load_toollist;



	pload_toollist load_toollist;
	bool load_toollist_intercept_enabled = false;



	static const char* testtoollist = "$CONTENT_f63543d9-d268-4052-ad87-de4c9dfef67a/Tools/ToolSets/test.json";


	void hook_load_toolsetlist(void* something, const char** file) {
		Console::log(Color::Aqua, "load_toolsetlist: something=[%p] file=[%s]", something, *file);

		// enable intercepting for the next load_toollist call
		load_toollist_intercept_enabled = true;

		((pload_toolsetlist)*hck_load_toolsetlist)(something, file);
	}

	void hook_load_toollist(ToolManager* toolManager, const char** file) {
		Console::log(Color::Aqua, "load_toollist: toolManager=[%p] file=[%s]", toolManager, *file);

		if (load_toollist_intercept_enabled) {
			// disable intercepting so we don't load our toollist multiple times (recursively)
			load_toollist_intercept_enabled = false;

			// temporarily store the original path
			const char* before = *file;
			size_t beforeLength = toolManager->toollistFileLength;

			// update the path with our path
			*file = testtoollist;
			toolManager->toollistFileLength = strlen(testtoollist);

			// load the toollist file
			load_toollist(toolManager, file);

			// restore the orginal path
			*file = before;
			toolManager->toollistFileLength = beforeLength;
		}

		return ((pload_toollist)*hck_load_toollist)(toolManager, file);
	}



	bool Install() {
		SignatureScanner sigScanner(L"ScrapMechanic.exe");
		if (!sigScanner.readMemory()) {
			Console::log(Color::LightRed, "Failed to read the memory of ScrapMechanic.exe");
			return false;
		}

		DWORD64 load_toolsetlist = sigScanner.scan("\x48\x89\x5C\x24\x18\x48\x89\x6C\x24\x20\x56\x57\x41\x56\x48\x81\xEC\x90\x00\x00\x00\x48\x8B\x00\x00\x00\x00\x00\x48\x33\xC4\x48\x89\x84\x24\x88\x00\x00\x00", "xxxxxxxxxxxxxxxxxxxxxxx?????xxxxxxxxxxx");
		if (!load_toolsetlist) {
			Console::log(Color::LightRed, "Unable to find load_toolsetlist in memory");
			return false;
		}

		hck_load_toolsetlist = GameHooks::Inject((void*)load_toolsetlist, &WorkshopTools::Hooks::hook_load_toolsetlist, 10);
		if (!hck_load_toolsetlist) {
			Console::log(Color::Red, "Failed to inject 'load_toolsetlist'");
			return false;
		}



		load_toollist = (pload_toollist)sigScanner.scan("\x48\x8B\xC4\x48\x89\x58\x18\x48\x89\x70\x20\x57\x41\x54\x41\x55\x41\x56\x41\x57\x48\x81\xEC\x50\x01\x00\x00", "xxxxxxxxxxxxxxxxxxxxxxxxxxx");
		if (!load_toollist) {
			Console::log(Color::LightRed, "Unable to find load_toollist in memory");
			return false;
		}

		Console::log(Color::Aqua, "Found load_toollist at [%p]", load_toollist);

		hck_load_toollist = GameHooks::Inject((void*)load_toollist, &WorkshopTools::Hooks::hook_load_toollist, 11);
		if (!hck_load_toollist) {
			Console::log(Color::Red, "Failed to inject 'load_toollist'");
			return false;
		}

		return true;
	}
}