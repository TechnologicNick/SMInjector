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
        undefined4* field7_0x10;
        undefined4* field8_0x18;
        undefined field9_0x20;
        undefined field10_0x21;
        undefined field11_0x22;
        undefined field12_0x23;
        undefined field13_0x24;
        undefined field14_0x25;
        undefined field15_0x26;
        undefined field16_0x27;
    public:
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
