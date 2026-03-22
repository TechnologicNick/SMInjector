#pragma once

#include "Types.hpp"

namespace SM {
	class GameInfo {
    public:
        uint32_t m_eGameMode;
        uint32_t m_uSeed;
        uint32_t m_uGameTick;
    private:
        undefined field3_0xc;
        undefined field4_0xd;
        undefined field5_0xe;
        undefined field6_0xf;
    public:
        std::vector<void*> m_vecUsedUgcIdPairs;
        std::string m_sGameScriptStorage;
        std::vector<void*> m_initializationScriptDataKeys;
        std::vector<void*> m_initializationGenericDataKeys;
        bool m_bDeveloperMode;
    private:
        undefined field21_0x79;
        undefined field22_0x7a;
        undefined field23_0x7b;
        undefined field24_0x7c;
        undefined field25_0x7d;
        undefined field26_0x7e;
        undefined field27_0x7f;
    public:
        std::string m_sSaveFilePath;
        std::vector<std::string> m_aFileChecksumPaths;
    };

    namespace {
        constexpr size_t GameInfo_size = sizeof(GameInfo);
        static_assert(sizeof(GameInfo) == 184, "GameInfo wrong size");
    }
}
