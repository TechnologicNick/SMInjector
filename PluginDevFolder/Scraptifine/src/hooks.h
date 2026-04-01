#pragma once

#include <Windows.h>
#include <type_traits>
#include <gamehook.h>
#include <vector>
#include <intrin.h>

#include "RTTI.h"
#include "Xrefs.h"

#include <console.h>
using Console::Color;

namespace Scraptifine::Hooks {
    using PROC_Thrd_yield = std::add_pointer<decltype(_Thrd_yield)>::type;

    GameHook* hck_target_Thrd_yield;

    void hook_target_Thrd_yield() {
        Console::log(Color::Aqua, "In hook_target_Thrd_yield!");

        // Call the original function
        return ((PROC_Thrd_yield)hck_target_Thrd_yield)();
	}

    bool InstallHooks() {
        Console::log(Color::Aqua, "Installing hooks...");

        const void* pSimplePhysicsTerrain_ScheduleCellFeatureUpdate = SMLibrary::Xrefs::FindFunctionReferencingString(GetModuleHandle(NULL), "pCell->getFeatures() != wantedFeatures || !reloadFeatures.empty()");
        if (!pSimplePhysicsTerrain_ScheduleCellFeatureUpdate) {
            Console::log(Color::Red, "Failed to find SimplePhysicsTerrain::ScheduleCellFeatureUpdate function");
            return false;
        }
        Console::log(Color::Aqua, "Found SimplePhysicsTerrain::ScheduleCellFeatureUpdate: %p", pSimplePhysicsTerrain_ScheduleCellFeatureUpdate);

        // =====================================================================
        // There are two calls to _Thrd_yield in ScrapMechanic.exe. We want to
        // hook the one in TerrainScheduleCellUpdate, but this function has no
        // unique string references.
        // 
        // The other function is in Contraption.cpp, and does have a unique
		// string reference, so we assert that there are exactly 2 calls to
		// _Thrd_yield and pick the one that is not referenced by the unique
        // string.
        FARPROC* p_Thrd_yield = SMLibrary::Xrefs::GetImportAddressTableEntry(GetModuleHandle(NULL), "msvcp140.dll", "_Thrd_yield");
		if (!p_Thrd_yield) {
			Console::log(Color::Red, "Failed to find IAT entry for _Thrd_yield");
			return false;
		}

        Console::log(Color::Aqua, "_Thrd_yield = %p", p_Thrd_yield);

		std::vector<void*> xrefs_Thrd_yield = SMLibrary::Xrefs::FindAllRipRelativeCallCodeReferencesToAddr(GetModuleHandle(NULL), p_Thrd_yield);
        for (void* ref : xrefs_Thrd_yield) {
            Console::log(Color::Aqua, "Found call to _Thrd_yield at %p", ref);
		}

        if (xrefs_Thrd_yield.size() != 2) {
            Console::log(Color::Red, "Expected to find exactly 2 xrefs to _Thrd_yield, but found %d", xrefs_Thrd_yield.size());
            return false;
		}

        const void* pWrongTarget = SMLibrary::Xrefs::FindFunctionReferencingString(GetModuleHandle(NULL), "pGameState != nullptr");
        if (!pWrongTarget) {
            Console::log(Color::Red, "Failed to find function referencing unique string for wrong _Thrd_yield Xref");
            return false;
		}

		void* target_Thrd_yield = nullptr;
		for (void* ref : xrefs_Thrd_yield) {
			const void* func = SMLibrary::Xrefs::FindFunctionStart(ref);
			if (!func) {
				Console::log(Color::Red, "Failed to find function start for xref to _Thrd_yield at %p", ref);
				return false;
			}

			if (pWrongTarget == func) {
                continue;
			}

			target_Thrd_yield = ref;
		}
		
        if (!target_Thrd_yield) {
			Console::log(Color::Red, "Failed to find target _Thrd_yield call in TerrainScheduleCellUpdate");
			return false;
		}

		Console::log(Color::Aqua, "Found target call to _Thrd_yield in TerrainScheduleCellUpdate at %p", target_Thrd_yield);

        hck_target_Thrd_yield = GameHooks::Inject(target_Thrd_yield, hook_target_Thrd_yield, 6);
        
        if (!hck_target_Thrd_yield) {
            Console::log(Color::Red, "Failed to inject '_Thrd_yield' in TerrainScheduleCellUpdate");
            return false;
        }

        Console::log(Color::Aqua, "Hooks installed!");
        return true;
    }

    bool UninstallHooks() {
        Console::log(Color::Aqua, "Hooks uninstalled!");
        return true;
    }
}
