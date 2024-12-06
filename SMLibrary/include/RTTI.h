#pragma once

#include <windows.h>
#include <dbghelp.h>
#include <vector>
#include <string>
#include <memory>
#include <stdexcept>
#include <system_error>
#include <rttidata.h>

#pragma comment(lib, "dbghelp.lib")

#include "console.h"
using Console::Color;

namespace SMLibrary::RTTI {
    struct FunctionArray {
		void* functions[1];
	};

    std::string Demangle(const char* mangledName) {
        if (!mangledName) {
            return "<invalid>";
        }

        char demangledName[1024] = { 0 };
        DWORD result = UnDecorateSymbolName(mangledName, demangledName, sizeof(demangledName), UNDNAME_COMPLETE);

        if (result == 0) {
            Console::log(Color::LightRed, "Failed to demangle symbol \"%s\". Error: %s", mangledName, std::system_category().message(GetLastError()).c_str());
            return "<invalid>";
        }

        return std::string(demangledName);
    }

    inline bool IsCompleteObjectLocatorValid(const _RTTICompleteObjectLocator* locator) {
        if (!locator || (uint64_t)locator == -1) {
			return false;
		}

		return locator->signature == COL_SIG_REV1 && locator->offset == 0 && locator->cdOffset == 0;
	}

    std::string GetDemangledClassName(const HMODULE moduleBase, const _RTTICompleteObjectLocator* pLocator) {
        TypeDescriptor* typeDesc = (TypeDescriptor*)((uint64_t)moduleBase + (uint64_t)pLocator->pTypeDescriptor);
        std::string className = Demangle(typeDesc->name);
        return className;
	}

    std::unordered_map<std::string, FunctionArray*> ParseRTTI(HMODULE moduleBase) {
        std::unordered_map<std::string, FunctionArray*> rttiMap;

        IMAGE_DOS_HEADER* dosHeader = (IMAGE_DOS_HEADER*)moduleBase;
        if (dosHeader->e_magic != IMAGE_DOS_SIGNATURE) {
            Console::log(Color::LightRed, "Failed to parse RTTI: Invalid DOS signature");
            return rttiMap;
        }

        IMAGE_NT_HEADERS* ntHeaders = (IMAGE_NT_HEADERS*)((BYTE*)moduleBase + dosHeader->e_lfanew);
        if (ntHeaders->Signature != IMAGE_NT_SIGNATURE) {
            Console::log(Color::LightRed, "Failed to parse RTTI: Invalid NT signature");
            return rttiMap;
        }

        IMAGE_SECTION_HEADER* section = IMAGE_FIRST_SECTION(ntHeaders);
        for (int i = 0; i < ntHeaders->FileHeader.NumberOfSections; ++i) {
            if (strncmp((char*)section->Name, ".rdata", 6) == 0) {
                BYTE* rdataBase = (BYTE*)moduleBase + section->VirtualAddress;
                DWORD rdataSize = section->Misc.VirtualSize;

                for (DWORD offset = 0; offset < rdataSize; offset += 8) {
                    uint64_t potentialLocator = (uint64_t)rdataBase + (uint64_t)offset;

                    if (
                        potentialLocator < (uint64_t)rdataBase ||
                        potentialLocator >= (uint64_t)rdataBase + rdataSize
                    ) {
						continue;
					}

                    _RTTICompleteObjectLocator* pLocator = *(_RTTICompleteObjectLocator**)potentialLocator;

                    if (
                        (uint64_t)pLocator < (uint64_t)rdataBase ||
                        (uint64_t)pLocator >= (uint64_t)rdataBase + rdataSize
                    ) {
                        continue;
                    }

					if (IsCompleteObjectLocatorValid(pLocator)) {
						std::string demangled = GetDemangledClassName(moduleBase, pLocator);
                        if (demangled != "<invalid>") {
                            rttiMap[demangled] = (FunctionArray*)(potentialLocator + sizeof(void*));
						}
					}
                }
            }
            ++section;
        }

        return rttiMap;
    }
}
