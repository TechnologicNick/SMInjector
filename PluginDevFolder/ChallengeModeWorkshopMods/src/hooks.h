#pragma once
#include <gamehook.h>
#include <sigscan.h>
//#include <rpcdce.h> // adds UUID/GUID

#include <console.h>
using Console::Color;

namespace ChallengeModeWorkshopMods::Hooks {

	typedef struct UGCId {
		unsigned long long fileId;
		unsigned char localId[16];
	};

	// https://stackoverflow.com/a/52337100/12586927
	typedef struct UGCIdVector {
		UGCId* begin;
		UGCId* end;
		UGCId* end_capacity;
	};

	typedef void (*pload_game_loop)(void*, void*);
	GameHook* hck_load_game_loop;

	typedef void (*pparse_shapesets_json)(void*, const char**);
	GameHook* hck_parse_shapesets_json;

	typedef int (*pload_workshop_mods)(void*, void*, void*);
	GameHook* hck_load_workshop_mods;

	DWORD64 pGameInstance;



	void log_ugc_items(UGCIdVector* items) {
		Console::log(Color::Aqua, "UGC items: begin=[%p], end=[%p], end_capacity=[%p]", items->begin, items->end, items->end_capacity);

		UGCId* current = items->begin;
		while (current < items->end) {
			Console::log(Color::Aqua, "UGC item: fileId=[%llu] localId=[%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x]", current->fileId,
				current->localId[ 0], current->localId[ 1], current->localId[ 2], current->localId[ 3],
				current->localId[ 4], current->localId[ 5], current->localId[ 6], current->localId[ 7],
				current->localId[ 8], current->localId[ 9], current->localId[10], current->localId[11],
				current->localId[12], current->localId[13], current->localId[14], current->localId[15]);

			current++;
		}
	}

	void hook_load_game_loop(void* gameInstance, void* result) {
		//Console::log(Color::Aqua, "load_game_loop: gameInstance=[%p] result=[%u, %llu]", gameInstance, result, ((DWORD64)result + 4));

		//log_ugc_items((UGCIdVector*)((DWORD64)gameInstance + 0x18));

		Hooks::pGameInstance = (DWORD64)gameInstance;

		((pload_game_loop)*hck_load_game_loop)(gameInstance, result);
	}

	void hook_parse_shapesets_json(void* something, const char** shapesetsJson) {
		Console::log(Color::Aqua, "parse_shapesets_json: something=[%p] shapesetsJson=[%s]", something, *shapesetsJson);

		if (strcmp(*shapesetsJson, "$CHALLENGE_DATA/Objects/Database/shapesets.json") == 0) {
			Console::log(Color::LightPurple, "Challenge mode detected!");

			// TODO: Load UGC items
		}

		((pparse_shapesets_json)*hck_parse_shapesets_json)(something, shapesetsJson);
	}

	int hook_load_workshop_mods(void* something, UGCIdVector* mods, void* something_else) {
		Console::log(Color::Aqua, "load_workshop_mods: something=[%p] mods=[%p] something_else[%p]", something, mods, something_else);

		log_ugc_items(mods);

		return ((pload_workshop_mods)*hck_load_workshop_mods)(something, mods, something_else);
	}



	bool Install() {
		SignatureScanner sigScanner(L"ScrapMechanic.exe");
		if (!sigScanner.readMemory()) {
			Console::log(Color::LightRed, "Failed to read the memory of ScrapMechanic.exe");
			return false;
		}



		DWORD64 load_game_loop = sigScanner.scan("\x48\x89\x5c\x24\x18\x55\x56\x57\x48\x83\xec\x50\x48\x8b\x05\xed\x72\xb9\x00\x48\x33\xc4\x48\x89\x44\x24\x40\x48\x8b\xda\x48\x8b\xf9\x8b\x0d\x39\x74\xb9\x00", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx");
		if (!load_game_loop) {
			Console::log(Color::LightRed, "Unable to find load_game_loop in memory");
			return false;
		}

		hck_load_game_loop = GameHooks::Inject((void*)load_game_loop, &ChallengeModeWorkshopMods::Hooks::hook_load_game_loop, 5);
		if (!hck_load_game_loop) {
			Console::log(Color::Red, "Failed to inject 'load_game_loop'");
			return false;
		}



		DWORD64 parse_shapesets_json = sigScanner.scan("\x48\x89\x5C\x24\x18\x55\x56\x57\x41\x54\x41\x55\x41\x56\x41\x57\x48\x8D\xAC\x24\xB0\xFD\xFF\xFF\x48\x81\xEC\x50\x03\x00\x00", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx");
		if (!parse_shapesets_json) {
			Console::log(Color::LightRed, "Unable to find parse_shapesets_json in memory");
			return false;
		}

		hck_parse_shapesets_json = GameHooks::Inject((void*)parse_shapesets_json, &ChallengeModeWorkshopMods::Hooks::hook_parse_shapesets_json, 5);
		if (!hck_parse_shapesets_json) {
			Console::log(Color::Red, "Failed to inject 'parse_shapesets_json'");
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