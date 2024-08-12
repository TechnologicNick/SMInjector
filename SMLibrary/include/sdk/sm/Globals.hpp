#pragma once

#include <Windows.h>
#include "Contraption.hpp"

namespace SM {
	static uintptr_t GetModuleBaseAddress() {
		return (uintptr_t)GetModuleHandle(NULL);
	}

	static Contraption** g_contraption = reinterpret_cast<Contraption**>(GetModuleBaseAddress() + 0x12A7618);

	constexpr int GameState_Null = 0;
	constexpr int GameState_LoadState = 1;
	constexpr int GameState_PlayState = 2;
	constexpr int GameState_MenuState = 3;
	constexpr int GameState_TileEditor = 4;
	constexpr int GameState_WorldBuilder = 5;
}
