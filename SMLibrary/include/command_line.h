#pragma once

#include <Windows.h>
#include <shellapi.h>

#include <optional>
#include <string>

namespace SMLibrary::CommandLine {
    inline std::optional<std::wstring> GetArgumentValue(const wchar_t* argumentName) {
        int argc = 0;
        LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);
        if (!argv) {
            return std::nullopt;
        }

        std::optional<std::wstring> result;

        for (int i = 1; i < argc; ++i) {
            if (_wcsicmp(argv[i], argumentName) == 0) {
                if (i + 1 < argc) {
                    result = argv[i + 1];
                }
                break;
            }
        }

        LocalFree(argv);
        return result;
    }

    inline bool HasArgument(const wchar_t* argumentName) {
        int argc = 0;
        LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);
        if (!argv) {
            return false;
        }

        bool found = false;
        for (int i = 1; i < argc; ++i) {
            if (_wcsicmp(argv[i], argumentName) == 0) {
                found = true;
                break;
            }
        }

        LocalFree(argv);
        return found;
    }
}
