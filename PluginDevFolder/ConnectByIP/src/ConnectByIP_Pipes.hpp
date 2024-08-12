#pragma once

#include <Windows.h>
#include <system_error>
#include <string>

namespace ConnectByIP::Pipes {

    HANDLE hPipe = INVALID_HANDLE_VALUE;

    std::wstring GetPipeName() {
        return std::wstring(L"\\\\.\\pipe\\ScrapMechanic_") + std::to_wstring(GetCurrentProcessId()) + L"_ConnectByIP";
    }

    std::wstring pipeName = GetPipeName();

    bool InitPipe() {
        if (hPipe != INVALID_HANDLE_VALUE) {
            Console::log(Color::LightRed, "Closing existing pipe");
            CloseHandle(hPipe);
        }

        hPipe = CreateNamedPipe(
            pipeName.c_str(),
            PIPE_ACCESS_DUPLEX,
            PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_NOWAIT,
            1,
            0x1000,
            0x1000,
            0,
            NULL
        );

        if (hPipe == INVALID_HANDLE_VALUE) {
            Console::log(Color::LightRed, "Failed to create named pipe: %s", std::system_category().message(GetLastError()).c_str());
            return false;
        }

        return true;
    }

    bool ReadConnectionString(std::string& connectionString) {
        if (hPipe == INVALID_HANDLE_VALUE) {
            Console::log(Color::LightRed, "Pipe not initialized");
            return false;
        }

        DWORD dwRead;
        char buffer[1024];
        if (!ReadFile(hPipe, buffer, sizeof(buffer), &dwRead, NULL)) {
            DWORD error = GetLastError();
            if (error != ERROR_PIPE_LISTENING) {
                Console::log(Color::LightRed, "Failed to read from pipe: %s (%d)", std::system_category().message(error).c_str(), error);
            }
            if (error == ERROR_BROKEN_PIPE) {
                InitPipe();
            }
            return false;
        }

        connectionString = std::string(buffer, dwRead);
        return true;
    }
}
