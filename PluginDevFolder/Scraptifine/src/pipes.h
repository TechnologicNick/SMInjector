#pragma once

#include <Windows.h>
#include <atomic>
#include <exception>
#include <optional>
#include <regex>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include "hooks.h"

#include <console.h>
using Console::Color;

namespace Scraptifine::Pipes {
    constexpr DWORD kPipeBufferSize = 0x1000;

    struct PipeRequest {
        std::string command;
        std::optional<int32_t> value;
    };

    HANDLE hPipe = INVALID_HANDLE_VALUE;
    std::thread pipeThread;
    std::atomic_bool stopRequested = false;

    std::string GetPipeName() {
        return std::string("\\\\.\\pipe\\ScrapMechanic_") + std::to_string(GetCurrentProcessId()) + "_Scraptifine";
    }

    std::wstring GetPipeNameWide() {
        return std::wstring(L"\\\\.\\pipe\\ScrapMechanic_") + std::to_wstring(GetCurrentProcessId()) + L"_Scraptifine";
    }

    std::string EscapeJson(const std::string& value) {
        std::string escaped;
        escaped.reserve(value.size());

        for (char ch : value) {
            switch (ch) {
            case '\\':
                escaped += "\\\\";
                break;
            case '"':
                escaped += "\\\"";
                break;
            case '\n':
                escaped += "\\n";
                break;
            case '\r':
                escaped += "\\r";
                break;
            case '\t':
                escaped += "\\t";
                break;
            default:
                escaped += ch;
                break;
            }
        }

        return escaped;
    }

    std::string BuildStatusJson(const bool ok, const std::optional<std::string>& error = std::nullopt) {
        const std::string pipeName = GetPipeName();
        const auto overrideWorkerCount = Hooks::GetOverrideWorkerCount();
        const std::vector<Hooks::BackendSnapshot> backends = Hooks::GetBackendSnapshots();

        std::ostringstream response;
        response << "{";
        response << "\"ok\":" << (ok ? "true" : "false");
        response << ",\"pid\":" << GetCurrentProcessId();
        response << ",\"pipe_name\":\"" << EscapeJson(pipeName) << "\"";
        response << ",\"override_worker_count\":";
        if (overrideWorkerCount.has_value()) {
            response << *overrideWorkerCount;
        } else {
            response << "null";
        }
        response << ",\"observed_backend_count\":" << backends.size();
        response << ",\"backends\":[";
        for (size_t i = 0; i < backends.size(); ++i) {
            const Hooks::BackendSnapshot& backend = backends[i];
            if (i != 0) {
                response << ",";
            }

            response << "{";
            response << "\"address\":\"" << EscapeJson(Hooks::FormatPointer(backend.address)) << "\"";
            response << ",\"first_seen_order\":" << backend.firstSeenOrder;
            response << ",\"last_game_requested\":";
            if (backend.lastGameRequested.has_value()) {
                response << *backend.lastGameRequested;
            } else {
                response << "null";
            }
            response << ",\"last_applied\":";
            if (backend.lastApplied.has_value()) {
                response << *backend.lastApplied;
            } else {
                response << "null";
            }
            response << "}";
        }
        response << "]";
        response << ",\"error\":";
        if (error.has_value()) {
            response << "\"" << EscapeJson(*error) << "\"";
        } else {
            response << "null";
        }
        response << "}";

        return response.str();
    }

    bool TryParseRequest(const std::string& payload, PipeRequest& request, std::string& error) {
        static const std::regex cmdRegex("\"cmd\"\\s*:\\s*\"([^\"]+)\"");
        static const std::regex valueRegex("\"value\"\\s*:\\s*(-?\\d+)");

        std::smatch match;
        if (!std::regex_search(payload, match, cmdRegex) || match.size() != 2) {
            error = "Missing string field 'cmd'";
            return false;
        }

        request.command = match[1].str();
        if (std::regex_search(payload, match, valueRegex) && match.size() == 2) {
            try {
                request.value = std::stoi(match[1].str());
            } catch (const std::exception&) {
                error = "Invalid integer field 'value'";
                return false;
            }
        } else {
            request.value.reset();
        }

        return true;
    }

    std::string HandleRequest(const std::string& payload) {
        PipeRequest request;
        std::string error;
        if (!TryParseRequest(payload, request, error)) {
            return BuildStatusJson(false, error);
        }

        if (request.command == "status") {
            return BuildStatusJson(true);
        }

        if (request.command == "set_worker_count") {
            if (!request.value.has_value()) {
                return BuildStatusJson(false, "Missing integer field 'value'");
            }

            if (*request.value < 1 || *request.value > 31) {
                return BuildStatusJson(false, "Worker count must be between 1 and 31");
            }

            if (!Hooks::ReapplyWorkerCounts(*request.value, &error)) {
                return BuildStatusJson(false, error);
            }

            return BuildStatusJson(true);
        }

        if (request.command == "clear_override") {
            if (!Hooks::ReapplyWorkerCounts(std::nullopt, &error)) {
                return BuildStatusJson(false, error);
            }

            return BuildStatusJson(true);
        }

        return BuildStatusJson(false, "Unknown command: " + request.command);
    }

    bool InitPipe() {
        if (hPipe != INVALID_HANDLE_VALUE) {
            CloseHandle(hPipe);
            hPipe = INVALID_HANDLE_VALUE;
        }

        hPipe = CreateNamedPipeW(
            GetPipeNameWide().c_str(),
            PIPE_ACCESS_DUPLEX,
            PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
            1,
            kPipeBufferSize,
            kPipeBufferSize,
            0,
            NULL
        );

        if (hPipe == INVALID_HANDLE_VALUE) {
            Console::log(Color::Red, "Failed to create Scraptifine pipe (error=%lu)", GetLastError());
            return false;
        }

        return true;
    }

    void ResetPipe() {
        if (hPipe != INVALID_HANDLE_VALUE) {
            DisconnectNamedPipe(hPipe);
            CloseHandle(hPipe);
            hPipe = INVALID_HANDLE_VALUE;
        }
    }

    void PipeThreadMain() {
        while (!stopRequested.load()) {
            if (hPipe == INVALID_HANDLE_VALUE && !InitPipe()) {
                return;
            }

            const BOOL connected = ConnectNamedPipe(hPipe, NULL);
            if (!connected && GetLastError() != ERROR_PIPE_CONNECTED) {
                if (!stopRequested.load()) {
                    Console::log(Color::Red, "ConnectNamedPipe failed (error=%lu)", GetLastError());
                }
                ResetPipe();
                continue;
            }

            char buffer[kPipeBufferSize] = {};
            DWORD bytesRead = 0;
            if (!ReadFile(hPipe, buffer, sizeof(buffer), &bytesRead, NULL)) {
                if (!stopRequested.load()) {
                    Console::log(Color::Red, "Failed to read Scraptifine pipe (error=%lu)", GetLastError());
                }
                ResetPipe();
                continue;
            }

            const std::string response = HandleRequest(std::string(buffer, bytesRead));

            DWORD bytesWritten = 0;
            if (!WriteFile(hPipe, response.data(), static_cast<DWORD>(response.size()), &bytesWritten, NULL) && !stopRequested.load()) {
                Console::log(Color::Red, "Failed to write Scraptifine pipe response (error=%lu)", GetLastError());
            }

            FlushFileBuffers(hPipe);
            ResetPipe();
        }

        ResetPipe();
    }

    void WakePipeServer() {
        HANDLE wakeHandle = CreateFileW(
            GetPipeNameWide().c_str(),
            GENERIC_READ | GENERIC_WRITE,
            0,
            NULL,
            OPEN_EXISTING,
            0,
            NULL
        );

        if (wakeHandle == INVALID_HANDLE_VALUE) {
            return;
        }

        DWORD pipeMode = PIPE_READMODE_MESSAGE;
        SetNamedPipeHandleState(wakeHandle, &pipeMode, NULL, NULL);

        static constexpr char wakeMessage[] = "{\"cmd\":\"status\"}";
        DWORD bytesWritten = 0;
        WriteFile(wakeHandle, wakeMessage, static_cast<DWORD>(sizeof(wakeMessage) - 1), &bytesWritten, NULL);

        char responseBuffer[kPipeBufferSize] = {};
        DWORD bytesRead = 0;
        ReadFile(wakeHandle, responseBuffer, sizeof(responseBuffer), &bytesRead, NULL);

        CloseHandle(wakeHandle);
    }

    bool StartPipeServer() {
        stopRequested = false;

        if (!InitPipe()) {
            return false;
        }

        pipeThread = std::thread(PipeThreadMain);
        Console::log(Color::Aqua, "Scraptifine pipe listening on %s", GetPipeName().c_str());
        return true;
    }

    void StopPipeServer() {
        stopRequested = true;
        WakePipeServer();

        if (pipeThread.joinable()) {
            pipeThread.join();
        }

        ResetPipe();
    }
}
