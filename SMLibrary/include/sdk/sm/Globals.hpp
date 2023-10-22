#pragma once

#include <Windows.h>
#include "Contraption.hpp"

namespace SM {
	static uintptr_t GetModuleBaseAddress() {
		return (uintptr_t)GetModuleHandle(NULL);
	}

	static Contraption** g_contraption = reinterpret_cast<Contraption**>(GetModuleBaseAddress() + 0x12A7618);
}
