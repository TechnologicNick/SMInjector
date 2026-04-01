#pragma once

#include <Windows.h>
#include <algorithm>
#include <cstdint>
#include <gamehook.h>
#include <mutex>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include "Xrefs.h"

#include <console.h>
using Console::Color;

namespace Scraptifine::Hooks {
    constexpr const char* kConcurrencyRuntimeModule = "concrt140.dll";
    constexpr const char* kSetConcurrencyLimitsImport = "?SetConcurrencyLimits@SchedulerPolicy@Concurrency@@QEAAXII@Z";

    using PROC_ParallelForPplBackend_SetWorkerCount = void(*)(void* backend, int32_t requestedWorkerCount);

    struct BackendInfo {
        uint64_t firstSeenOrder = 0;
        std::optional<int32_t> lastGameRequested;
        std::optional<int32_t> lastApplied;
    };

    struct BackendSnapshot {
        uintptr_t address = 0;
        uint64_t firstSeenOrder = 0;
        std::optional<int32_t> lastGameRequested;
        std::optional<int32_t> lastApplied;
    };

    struct HookDecision {
        bool isNewBackend = false;
        int32_t appliedWorkerCount = 0;
    };

    GameHook* hck_ParallelForPplBackend_SetWorkerCount = nullptr;
    std::mutex mtx_Backends;
    std::unordered_map<uintptr_t, BackendInfo> map_ObservedBackends;
    std::optional<int32_t> opt_OverrideWorkerCount;
    uint64_t nextBackendOrder = 1;
    bool hooksEnabled = false;

    std::string FormatPointer(const uintptr_t value) {
        std::ostringstream stream;
        stream << "0x" << std::hex << value;
        return stream.str();
    }

    HookDecision RegisterBackendCall(void* backend, const int32_t requestedWorkerCount) {
        const uintptr_t backendAddress = reinterpret_cast<uintptr_t>(backend);

        std::lock_guard<std::mutex> lock(mtx_Backends);
        auto& info = map_ObservedBackends[backendAddress];
        const bool isNewBackend = info.firstSeenOrder == 0;
        if (isNewBackend) {
            info.firstSeenOrder = nextBackendOrder++;
        }

        info.lastGameRequested = requestedWorkerCount;

        return {
            .isNewBackend = isNewBackend,
            .appliedWorkerCount = opt_OverrideWorkerCount.value_or(requestedWorkerCount),
        };
    }

    void RecordAppliedWorkerCount(void* backend, const int32_t appliedWorkerCount) {
        const uintptr_t backendAddress = reinterpret_cast<uintptr_t>(backend);

        std::lock_guard<std::mutex> lock(mtx_Backends);
        const auto iter = map_ObservedBackends.find(backendAddress);
        if (iter != map_ObservedBackends.end()) {
            iter->second.lastApplied = appliedWorkerCount;
        }
    }

    std::vector<BackendSnapshot> GetBackendSnapshots() {
        std::vector<BackendSnapshot> backends;

        std::lock_guard<std::mutex> lock(mtx_Backends);
        backends.reserve(map_ObservedBackends.size());
        for (const auto& [address, info] : map_ObservedBackends) {
            backends.push_back({
                .address = address,
                .firstSeenOrder = info.firstSeenOrder,
                .lastGameRequested = info.lastGameRequested,
                .lastApplied = info.lastApplied,
            });
        }

        std::sort(backends.begin(), backends.end(), [](const BackendSnapshot& left, const BackendSnapshot& right) {
            return left.firstSeenOrder < right.firstSeenOrder;
        });

        return backends;
    }

    std::optional<int32_t> GetOverrideWorkerCount() {
        std::lock_guard<std::mutex> lock(mtx_Backends);
        return opt_OverrideWorkerCount;
    }

    bool ReapplyWorkerCounts(const std::optional<int32_t> overrideWorkerCount, std::string* error = nullptr) {
        struct ReapplyTarget {
            void* backend = nullptr;
            int32_t workerCount = 0;
        };

        std::vector<ReapplyTarget> targets;
        {
            std::lock_guard<std::mutex> lock(mtx_Backends);
            opt_OverrideWorkerCount = overrideWorkerCount;

            for (const auto& [address, info] : map_ObservedBackends) {
                if (overrideWorkerCount.has_value()) {
                    targets.push_back({
                        .backend = reinterpret_cast<void*>(address),
                        .workerCount = *overrideWorkerCount,
                    });
                    continue;
                }

                if (info.lastGameRequested.has_value()) {
                    targets.push_back({
                        .backend = reinterpret_cast<void*>(address),
                        .workerCount = *info.lastGameRequested,
                    });
                }
            }
        }

        auto original = reinterpret_cast<PROC_ParallelForPplBackend_SetWorkerCount>(hck_ParallelForPplBackend_SetWorkerCount);
        if (!original) {
            if (targets.empty()) {
                return true;
            }

            if (error) {
                *error = "Original ParallelForPplBackend_SetWorkerCount trampoline is not available";
            }
            return false;
        }

        for (const ReapplyTarget& target : targets) {
            Console::log(Color::Aqua, "Reapplying worker count %d to backend %p", target.workerCount, target.backend);
            original(target.backend, target.workerCount);
            RecordAppliedWorkerCount(target.backend, target.workerCount);
        }

        return true;
    }

    void hook_ParallelForPplBackend_SetWorkerCount(void* backend, const int32_t requestedWorkerCount) {
        auto original = reinterpret_cast<PROC_ParallelForPplBackend_SetWorkerCount>(hck_ParallelForPplBackend_SetWorkerCount);
        if (!original) {
            Console::log(Color::Red, "ParallelForPplBackend_SetWorkerCount trampoline is unavailable");
            return;
        }

        if (!hooksEnabled) {
            original(backend, requestedWorkerCount);
            return;
        }

        const HookDecision decision = RegisterBackendCall(backend, requestedWorkerCount);
        if (decision.isNewBackend) {
            Console::log(Color::Aqua, "Observed ParallelFor backend at %p", backend);
        }

        original(backend, decision.appliedWorkerCount);
        RecordAppliedWorkerCount(backend, decision.appliedWorkerCount);
    }

    bool InstallHooks() {
        Console::log(Color::Aqua, "Installing hooks...");

        FARPROC* pSetConcurrencyLimits = SMLibrary::Xrefs::GetImportAddressTableEntry(
            GetModuleHandle(NULL),
            kConcurrencyRuntimeModule,
            kSetConcurrencyLimitsImport
        );
        if (!pSetConcurrencyLimits) {
            return false;
        }

        Console::log(Color::Aqua, "Found IAT entry for '%s' at %p", kSetConcurrencyLimitsImport, pSetConcurrencyLimits);

        std::vector<void*> xrefs = SMLibrary::Xrefs::FindAllRipRelativeCallCodeReferencesToAddr(GetModuleHandle(NULL), pSetConcurrencyLimits);
        for (void* ref : xrefs) {
            Console::log(Color::Aqua, "Found call to SetConcurrencyLimits at %p", ref);
        }

        if (xrefs.size() != 2) {
            Console::log(Color::Red, "Expected exactly 2 xrefs to '%s', found %d", kSetConcurrencyLimitsImport, xrefs.size());
            return false;
        }

        const void* functionStart = SMLibrary::Xrefs::FindFunctionStart(xrefs[0]);
        if (!functionStart) {
            Console::log(Color::Red, "Failed to resolve function start for xref %p", xrefs[0]);
            return false;
        }

        const void* secondFunctionStart = SMLibrary::Xrefs::FindFunctionStart(xrefs[1]);
        if (!secondFunctionStart) {
            Console::log(Color::Red, "Failed to resolve function start for xref %p", xrefs[1]);
            return false;
        }

        if (functionStart != secondFunctionStart) {
            Console::log(Color::Red, "SetConcurrencyLimits xrefs resolve to different functions: %p and %p", functionStart, secondFunctionStart);
            return false;
        }

        Console::log(Color::Aqua, "ParallelForPplBackend_SetWorkerCount starts at %p", functionStart);

        hck_ParallelForPplBackend_SetWorkerCount = GameHooks::Inject(const_cast<void*>(functionStart), hook_ParallelForPplBackend_SetWorkerCount, 5);
        if (!hck_ParallelForPplBackend_SetWorkerCount) {
            Console::log(Color::Red, "Failed to inject ParallelForPplBackend_SetWorkerCount");
            return false;
        }

        hooksEnabled = true;
        Console::log(Color::Aqua, "Hooks installed!");
        return true;
    }

    bool UninstallHooks() {
        hooksEnabled = false;

        std::string error;
        if (!ReapplyWorkerCounts(std::nullopt, &error)) {
            Console::log(Color::Red, "Failed to clear override during unload: %s", error.c_str());
        }

        Console::log(Color::Aqua, "Hooks disabled");
        return true;
    }
}
