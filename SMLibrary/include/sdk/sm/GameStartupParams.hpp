#pragma once

#include "Types.hpp"
#include "GameInfo.hpp"

namespace SM {
    class GameStartupParams {
    public:
        bool m_bListenServer;
    private:
        undefined field1_0x1;
        undefined field2_0x2;
        undefined field3_0x3;
        undefined field4_0x4;
        undefined field5_0x5;
        undefined field6_0x6;
        undefined field7_0x7;
    public:
        uint64_t m_uConnectSteamId;
        std::string m_sPassphraseUuid;
        GameInfo m_gameInfo;
    };

    namespace {
        constexpr size_t GameStartupParams_size = sizeof(GameStartupParams);
        static_assert(sizeof(GameStartupParams) == 232, "GameStartupParams wrong size");
    }
}
