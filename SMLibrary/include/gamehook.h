#pragma once

#include "stdafx.h"

typedef void* GameHook;
typedef long long longlong;

#ifndef _SM_LIBRARY_BUILD_PLUGIN
#include <windows.h>
#include <map>
#endif

#include "../include/console.h"
using Console::Color;

namespace GameHooks {
#ifndef _SM_LIBRARY_BUILD_PLUGIN

	// Struct describing the hook
	struct GateContext {
		// The address of the hooked function
		void* function;

		// The length in bytes of the hook
		size_t length;

		// The allocated page within 2GB
		void* page_address;

		// The gate that should be called
		void* end_gate;

		// Last hook injected
		GameHook* last_hook;
	};

	// We need to specify a map that contains information about where we have hooked stuff previously
	std::map<void*, GateContext*> hooked_map;

	void* AllocatePageWithin2GB(void* target_address, int length) {
		static ULONG dwAllocationGranularity;

		// Fetch some allocation size
		if(!dwAllocationGranularity) {
			SYSTEM_INFO si;
			GetSystemInfo(&si);
			dwAllocationGranularity = si.dwAllocationGranularity;
		}

		UINT_PTR address = (UINT_PTR)target_address;
		SIZE_T dwSize = length;
		
		UINT_PTR min, max, addr, add = dwAllocationGranularity - 1, mask = ~add;
		min = address >= 0x80000000 ? (address - 0x80000000 + add) & mask : 0;
		max = address < (UINTPTR_MAX - 0x80000000) ? (address + 0x80000000) & mask : UINTPTR_MAX;

		::MEMORY_BASIC_INFORMATION mbi; 
		do {
			// Query information about the currently requested memory
			if(!VirtualQuery((void*)min, &mbi, sizeof(mbi))) return nullptr;

			// Spooky stuff 
			min = (UINT_PTR)mbi.BaseAddress + mbi.RegionSize;

			if(mbi.State == MEM_FREE) {
				addr = ((UINT_PTR)mbi.BaseAddress + add) & mask;

				if(addr < min && dwSize <= (min - addr)) {
					if(addr = (UINT_PTR)VirtualAlloc((PVOID)addr, dwSize, MEM_COMMIT|MEM_RESERVE, PAGE_EXECUTE_READWRITE)) {
						return (PVOID)addr;
					}
				}
			}
		} while (min < max);

		return nullptr;
	}
	
	GateContext* CreateInjectionHook(void* target_function, int length) {
		GateContext* context = new GateContext();
		context->function = target_function;
		context->length = length;
		context->page_address = AllocatePageWithin2GB(target_function, length + 28);
		context->end_gate = (void*)((long long)context->page_address + 14);
		// context.last_hook

		return context;
	}

	// Modify context to inject gate
	
	bool InjectGate(GateContext* context, void *dst, void *src) {
		typedef long long longlong;
		
		size_t len = context->length;
		void* gate = context->page_address;
		
		// Make the first jump into the target method
		*(longlong*)((longlong)gate) = 0x25FF; // Add far jump
		*(longlong*)((longlong)gate + 6) = (longlong)src;

		// Store the first 'len' bytes of the function into the newly created gate
		memcpy((void*)((longlong)gate + 14), dst, len);
		// Construct the far jump to the begining of the hooked function
		*(longlong*)((longlong)gate + len + 14) = 0x25FF; // Add far jump
		*(longlong*)((longlong)gate + len + 20) = (longlong)dst + len;

		DWORD oldProtection;
		// Update the protection for the gate memory
		VirtualProtect(gate, (size_t)len + 6, PAGE_EXECUTE_READ, &oldProtection);
	
		// Allow modifications of the target function
		VirtualProtect(dst, (size_t)len, PAGE_EXECUTE_READWRITE, &oldProtection);

		memset(dst, 0x90, len); // Fill the replaced region with NOP

		// Modify the target function
		// page_address - target_addres - 5

		// Make the first 5 bytes point towards the page with the absolute jump
		*(char*)((longlong)dst) = (char)0xE9;
		// Make sure this is within the 2GB range !!!!!!!!
		*(int*)((longlong)dst + 1) = (int)((longlong)context->page_address - (longlong)dst - 5);
	
		DWORD temp;
		VirtualProtect(dst, (size_t)len, oldProtection, &temp);
		
		GameHook* gate_hook = new GameHook();
		*((void**)gate_hook) = context->end_gate;
		context->last_hook = gate_hook;

		return true;
	}

	_LIB_EXPORT GameHook* Inject(void* target_function, void* hook_function, int length) {
		// First we check if we have already hooked the function
		auto iter = hooked_map.find(target_function);
		if(iter != hooked_map.end()) {
			// target function was already injected
			GateContext* context = iter->second;

			// Modify the last hooks gate to point to the new function
			*((void**)context->last_hook) = hook_function;

			// Modify the next hook to point towards the end gate
			GameHook* next_hook = new GameHook();
			*((void**)next_hook) = context->end_gate;

			// Update the last injected hook
			context->last_hook = next_hook;

			return next_hook;
		} else {
			GateContext* new_context = CreateInjectionHook(target_function, length);

			if(!InjectGate(new_context, target_function, hook_function)) {
				return nullptr;
			}

			hooked_map[target_function] = new_context;
			return new_context->last_hook;
		}
	}

	_LIB_EXPORT	GameHook* InjectFromName(const char* module_name, const char* proc_name, int offset, void* hook_function, int length) {
		HMODULE hModule = GetModuleHandleA(module_name);
		if (!hModule) {
			Console::log(Color::LightRed, "[InjectFromName] The module '%s' was not found\n", module_name);
			return nullptr;
		}

		FARPROC target = GetProcAddress(hModule, proc_name);
		if (!target) {
			Console::log(Color::LightRed, "[InjectFromName] The function '%s' was not found in module '%s'\n", proc_name, module_name);
			return nullptr;
		}

		return GameHooks::Inject((void*)((uint64_t)target + offset), hook_function, length);
	}

	_LIB_EXPORT	GameHook* InjectFromName(const char* module_name, const char* proc_name, void* hook_function, int length) {
		return GameHooks::InjectFromName(module_name, proc_name, 0, hook_function, length);
	}
#else
	_LIB_IMPORT GameHook* InjectFromName(const char* module_name, const char* proc_name, void* hook_function, int length);
	_LIB_IMPORT GameHook* Inject(void* target_function, void* hook_function, int length);
#endif

}
