#pragma once
#include <gamehook.h>
#include <sigscan.h>
//#include <rpcdce.h> // adds UUID/GUID

#include <console.h>
using Console::Color;

namespace ChallengeModeWorkshopMods::Hooks {

	typedef struct WorkshopModId {
		unsigned long long fileId;
		unsigned char localId[16];
	};

	// https://stackoverflow.com/a/52337100/12586927
	typedef struct WorkshopModIdVector {
		WorkshopModId* begin;
		WorkshopModId* end;
		WorkshopModId* end_capacity;
	};

	typedef void (*pload_workshop_mods)(void*, void*, void*);
	GameHook* hck_load_workshop_mods;



	void hook_load_workshop_mods(void* something, WorkshopModIdVector* mods, void* something_else) {
		Console::log(Color::Aqua, "load_toolsetlist: something=[%p] mods=[%p] something_else[%p]", something, mods, something_else);

		Console::log(Color::Aqua, "begin=[%p], end=[%p], end_capacity=[%p]", mods->begin, mods->end, mods->end_capacity);

		WorkshopModId* currentMod = mods->begin;
		while (currentMod < mods->end) {
			Console::log(Color::Aqua, "Mod: fileId=[%llu] localId=[%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x]", currentMod->fileId,
				currentMod->localId[0], currentMod->localId[1], currentMod->localId[2], currentMod->localId[3],
				currentMod->localId[4], currentMod->localId[5], currentMod->localId[6], currentMod->localId[7],
				currentMod->localId[8], currentMod->localId[9], currentMod->localId[10], currentMod->localId[11],
				currentMod->localId[12], currentMod->localId[13], currentMod->localId[14], currentMod->localId[15]);

			currentMod++;
		}

		((pload_workshop_mods)*hck_load_workshop_mods)(something, mods, something_else);
	}



	bool Install() {
		SignatureScanner sigScanner(L"ScrapMechanic.exe");
		if (!sigScanner.readMemory()) {
			Console::log(Color::LightRed, "Failed to read the memory of ScrapMechanic.exe");
			return false;
		}

		DWORD64 load_workshop_mods = sigScanner.scan("\x48\x89\x5C\x24\x18\x55\x56\x57\x41\x54\x41\x55\x41\x56\x41\x57\x48\x8D\xAC\x24\x50\xFD\xFF\xFF\x48\x81\xEC\xB0\x03\x00\x00\x48\x8B\x00\x00\x00\x00\x00\x48\x33\xC4\x48\x89\x85\xA0\x02\x00\x00\x41\x8B\xD8\x89\x5C\x24\x68\x4C\x8B\xF1", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?????xxxxxxxxxxxxxxxxxxxx");
		if (!load_workshop_mods) {
			Console::log(Color::LightRed, "Unable to find load_workshop_mods in memory");
			return false;
		}

		hck_load_workshop_mods = GameHooks::Inject((void*)load_workshop_mods, &ChallengeModeWorkshopMods::Hooks::hook_load_workshop_mods, 5);
		if (!hck_load_workshop_mods) {
			Console::log(Color::Red, "Failed to inject 'load_workshop_mods'");
			return false;
		}

		return true;
	}
}