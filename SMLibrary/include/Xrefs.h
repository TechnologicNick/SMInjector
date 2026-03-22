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
