#pragma once

#include <windows.h>
#include <vector>
#include <string>
#include <memory>
#include <system_error>

#include "console.h"
using Console::Color;

namespace SMLibrary::Xrefs {

    /// <summary>
	/// Retrieves the address of an entry in the Import Address Table (IAT) of a module. Note that this function only works for functions that are imported by name, not by ordinal.
    /// </summary>
	/// <param name="hModule">The handle to the module whose IAT entry is to be retrieved.</param>
	/// <param name="lpModuleName">The name of the module from which the function is imported (e.g. "msvcp140.dll").</param>
	/// <param name="lpProcName">The name of the function to retrieve.</param>
	/// <returns>A pointer to the function's address, or NULL if not found.</returns>
    FARPROC* GetImportAddressTableEntry(HMODULE hModule, LPCSTR lpModuleName, LPCSTR lpProcName) {
		// Get the address of the Import Address Table (IAT)
		PIMAGE_DOS_HEADER pDosHeader = (PIMAGE_DOS_HEADER)hModule;
		PIMAGE_NT_HEADERS pNtHeaders = (PIMAGE_NT_HEADERS)((BYTE*)hModule + pDosHeader->e_lfanew);
		PIMAGE_IMPORT_DESCRIPTOR pImportDescriptor = (PIMAGE_IMPORT_DESCRIPTOR)((BYTE*)hModule + pNtHeaders->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress);

		// Iterate through the import descriptors to find the module
		while (pImportDescriptor->Name) {
			const char* currentModuleName = (const char*)((BYTE*)hModule + pImportDescriptor->Name);
			// Console::log(Color::Gray, "Module: %s", currentModuleName);
			if (!_stricmp(currentModuleName, lpModuleName)) {
				break;
			}
			pImportDescriptor++;
		}

		// If the module was not found, return NULL
		if (!pImportDescriptor->Name) {
			Console::log(Color::LightRed, "[GetImportAddressTableEntry] The module '%s' was not found in the import address table", lpModuleName);
			return NULL;
		}

		// On loaded images:
		//   OriginalFirstThunk points to the name or ordinal of the imported function.
		//   FirstThunk points to the resolved function address.
		PIMAGE_THUNK_DATA pOriginalThunk = (PIMAGE_THUNK_DATA)((BYTE*)hModule + pImportDescriptor->OriginalFirstThunk);
		PIMAGE_THUNK_DATA pResolvedThunk = (PIMAGE_THUNK_DATA)((BYTE*)hModule + pImportDescriptor->FirstThunk);

		// Iterate through the thunk table of hModule to find the function.
		while (pOriginalThunk->u1.AddressOfData && pResolvedThunk->u1.AddressOfData) {

			// If the thunk is imported by name
			if ((pOriginalThunk->u1.AddressOfData & IMAGE_ORDINAL_FLAG) == 0) {
				PIMAGE_IMPORT_BY_NAME pImportByName = (PIMAGE_IMPORT_BY_NAME)((BYTE*)hModule + pOriginalThunk->u1.AddressOfData);
				// Console::log(Color::Gray, "  Function: %s", pImportByName->Name);
				if (!_stricmp(pImportByName->Name, lpProcName)) {
					return (FARPROC*)&(pResolvedThunk->u1.Function);
				}
			}
			else {
				// If the thunk is imported by ordinal
				// Console::log(Color::Gray, "  Ordinal: %d", pOriginalThunk->u1.Ordinal);
			}

			pOriginalThunk++;
			pResolvedThunk++;
		}

		// If the function was not found, return NULL
		Console::log(Color::LightRed, "[GetImportAddressTableEntry] The function '%s' was not found in module '%s'", lpProcName, lpModuleName);
		return NULL;
	}

    /// <summary>
    /// Finds the first occurrence of a byte pattern in a module.
    /// </summary>
    /// <param name="moduleBase">The base address of the module to search.</param>
    /// <param name="str">The byte pattern to search for.</param>
    /// <returns>The address of the first occurrence of the byte pattern, or nullptr if not found.</returns>
    const char* FindStringConstant(const HMODULE moduleBase, const std::string& str) {
		IMAGE_DOS_HEADER* dosHeader = (IMAGE_DOS_HEADER*)moduleBase;
		if (dosHeader->e_magic != IMAGE_DOS_SIGNATURE) {
			Console::log(Color::LightRed, "Failed to find string constant: Invalid DOS signature");
			return nullptr;
		}

		IMAGE_NT_HEADERS* ntHeaders = (IMAGE_NT_HEADERS*)((BYTE*)moduleBase + dosHeader->e_lfanew);
		if (ntHeaders->Signature != IMAGE_NT_SIGNATURE) {
			Console::log(Color::LightRed, "Failed to find string constant: Invalid NT signature");
			return nullptr;
		}

		IMAGE_SECTION_HEADER* section = IMAGE_FIRST_SECTION(ntHeaders);
		for (int i = 0; i < ntHeaders->FileHeader.NumberOfSections; ++i) {
			if (strncmp((char*)section->Name, ".rdata", 6) == 0) {
				BYTE* rdataBase = (BYTE*)moduleBase + section->VirtualAddress;
				DWORD rdataSize = section->Misc.VirtualSize;

				for (DWORD offset = 0; offset < rdataSize; ++offset) {
					const char* potentialString = (const char*)rdataBase + offset;
					if (memcmp(potentialString, str.c_str(), str.size()) == 0) {
						return potentialString;
					}
				}
			}
			++section;
		}

		return nullptr;
	}

    /// <summary>
    /// Finds all code references to a given address in a module. This function is not guaranteed to find all references.
    /// </summary>
    /// <param name="moduleBase">The base address of the module to search.</param>
    /// <param name="target">The address to search for.</param>
    /// <returns>A vector of pointers to the addresses of the code references.</returns>
    std::vector<void*> FindAllRelativeLeaCodeReferencesToAddr(const HMODULE moduleBase, const void* target) {
        std::vector<void*> references;

        IMAGE_DOS_HEADER* dosHeader = (IMAGE_DOS_HEADER*)moduleBase;
        if (dosHeader->e_magic != IMAGE_DOS_SIGNATURE) {
            Console::log(Color::LightRed, "Failed to find references: Invalid DOS signature");
            return references;
        }

        IMAGE_NT_HEADERS* ntHeaders = (IMAGE_NT_HEADERS*)((BYTE*)moduleBase + dosHeader->e_lfanew);
        if (ntHeaders->Signature != IMAGE_NT_SIGNATURE) {
            Console::log(Color::LightRed, "Failed to find references: Invalid NT signature");
            return references;
        }

        IMAGE_SECTION_HEADER* section = IMAGE_FIRST_SECTION(ntHeaders);
        for (int i = 0; i < ntHeaders->FileHeader.NumberOfSections; ++i) {
            if (strncmp((char*)section->Name, ".text", 5) == 0) {
                const size_t rdataBase = (size_t)moduleBase + section->VirtualAddress;
                const size_t rdataSize = (size_t)section->Misc.VirtualSize;

                // https://gchq.github.io/CyberChef/#recipe=Disassemble_x86('64','Full%20x86%20architecture',16,0,true,false)&input=NDg4ZDA1MWJjYjZlMDA&oeol=CRLF
                const uint16_t leaOpcode = 0x8D48; // 48 8D

                for (size_t ptr = rdataBase; ptr < rdataBase + rdataSize - 2; ptr += 1) {
                    if (*(uint16_t*)ptr == leaOpcode) {
						const int32_t offset = *(uint32_t*)(ptr + 3) + 7; // +7 to account for the length of the instruction, as the offset is relative to the next instruction
                        if (ptr + offset == (size_t)target) {
							references.push_back((void*)ptr);
						}
					}
                }
            }
            ++section;
        }

        return references;
    }

    /// <summary>
    /// Finds the start of a function given a pointer inside the function.
    /// </summary>
    /// <param name="ptrInsideFunction">The pointer inside the function.</param>
    /// <returns>The address of the start of the function, or nullptr if not found.</returns>
    const void* FindFunctionStart(const void* ptrInsideFunction) {
        DWORD64 base;
        UNWIND_HISTORY_TABLE historyTable;

        const PRUNTIME_FUNCTION func = RtlLookupFunctionEntry((DWORD64)ptrInsideFunction, &base, &historyTable);
        if (!func) {
			return nullptr;
		}

        const uint64_t functionStart = base + func->BeginAddress;
        return (void*)functionStart;
	}

    /// <summary>
    /// Finds the start of a function that references a given string.
    /// </summary>
    /// <param name="moduleBase">The base address of the module to search.</param>
    /// <param name="str">The string to search for.</param>
    /// <returns>The address of the start of the function, or nullptr if not found.</returns>
    const void* FindFunctionReferencingString(const HMODULE moduleBase, const std::string& str) {
        const char* target = SMLibrary::Xrefs::FindStringConstant(GetModuleHandle(NULL), str);
        if (!target) {
            Console::log(Color::Red, "Failed to find string '%s' in .rdata section!", str.c_str());
            return nullptr;
        }

        const std::vector<void*> xrefs = SMLibrary::Xrefs::FindAllRelativeLeaCodeReferencesToAddr(GetModuleHandle(NULL), target);
        if (xrefs.size() == 0) {
            Console::log(Color::Red, "Failed to find any xrefs to string '%s' in .text section!", str.c_str());
            return nullptr;
        }
        if (xrefs.size() > 1) {
            Console::log(Color::Red, "Found more than one xref to string '%s' in .text section!", str.c_str());
            return nullptr;
        }

        const void* start = SMLibrary::Xrefs::FindFunctionStart(xrefs[0]);
        if (!start) {
            Console::log(Color::Red, "Failed to find function start for xref to string '%s' in .text section!", str.c_str());
            return nullptr;
        }

        return start;
    }
}
