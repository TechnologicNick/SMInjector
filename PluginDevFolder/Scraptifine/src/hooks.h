#pragma once

#include <Windows.h>
#include <shellapi.h>

#include <optional>

#include "Xrefs.h"

#include <console.h>
using Console::Color;

namespace Scraptifine::Hooks {
    constexpr unsigned int kDefaultThreadCount = 4;

    using PROC_GetProcessorCount = unsigned int(__cdecl*)();

    FARPROC* pIat_GetProcessorCount = nullptr;
    PROC_GetProcessorCount original_GetProcessorCount = nullptr;
    std::optional<unsigned int> opt_ForcedThreadCount;

    std::optional<unsigned int> ParseThreadCountFromCommandLine() {
        int argc = 0;
        LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);
        if (!argv) {
            Console::log(Color::Red, "CommandLineToArgvW failed");
            return 4;
        }

        std::optional<unsigned int> result;

        for (int i = 0; i < argc; ++i) {
            const wchar_t* arg = argv[i];
            if (_wcsicmp(arg, L"-threads") == 0) {
                if (i + 1 >= argc) {
                    Console::log(Color::Red, "Missing value after -threads");
                    break;
                }

                wchar_t* endPtr = nullptr;
                const unsigned long parsed = wcstoul(argv[i + 1], &endPtr, 10);
                if (endPtr == argv[i + 1] || *endPtr != L'\0' || parsed == 0 || parsed > 256) {
                    Console::log(Color::Red, "Invalid -threads value: %S", argv[i + 1]);
                    break;
                }

                result = static_cast<unsigned int>(parsed);
                break;
            }

        }

        LocalFree(argv);
        return result;
    }

    unsigned int __cdecl hook_GetProcessorCount() {
        if (opt_ForcedThreadCount.has_value()) {
            return *opt_ForcedThreadCount;
        }

        if (original_GetProcessorCount) {
            return original_GetProcessorCount();
        }

        return 0;
    }

    bool InstallHooks() {
        Console::log(Color::Aqua, "Installing hooks...");

        opt_ForcedThreadCount = ParseThreadCountFromCommandLine();
        if (!opt_ForcedThreadCount.has_value()) {
            opt_ForcedThreadCount = kDefaultThreadCount;
        }

        pIat_GetProcessorCount = SMLibrary::Xrefs::GetImportAddressTableEntry(
            GetModuleHandle(NULL),
            "concrt140.dll",
            "?GetProcessorCount@Concurrency@@YAIXZ"
        );
        if (!pIat_GetProcessorCount) {
            Console::log(Color::Red, "Failed to find IAT entry for ?GetProcessorCount@Concurrency@@YAIXZ");
            return false;
        }

        DWORD oldProtection = 0;
        if (!VirtualProtect(pIat_GetProcessorCount, sizeof(FARPROC), PAGE_EXECUTE_READWRITE, &oldProtection)) {
            Console::log(Color::Red, "Failed to make GetProcessorCount IAT entry writable");
            return false;
        }

        original_GetProcessorCount = reinterpret_cast<PROC_GetProcessorCount>(*pIat_GetProcessorCount);
        *pIat_GetProcessorCount = reinterpret_cast<FARPROC>(hook_GetProcessorCount);

        DWORD temp = 0;
        VirtualProtect(pIat_GetProcessorCount, sizeof(FARPROC), oldProtection, &temp);

        Console::log(Color::Aqua, "Forced Concurrency::GetProcessorCount to %u", *opt_ForcedThreadCount);
        Console::log(Color::Aqua, "Hooks installed!");
        return true;
    }

    bool UninstallHooks() {
        if (pIat_GetProcessorCount && original_GetProcessorCount) {
            DWORD oldProtection = 0;
            if (VirtualProtect(pIat_GetProcessorCount, sizeof(FARPROC), PAGE_EXECUTE_READWRITE, &oldProtection)) {
                *pIat_GetProcessorCount = reinterpret_cast<FARPROC>(original_GetProcessorCount);
                DWORD temp = 0;
                VirtualProtect(pIat_GetProcessorCount, sizeof(FARPROC), oldProtection, &temp);
            }
        }

        Console::log(Color::Aqua, "Hooks uninstalled!");
        return true;
    }
}
