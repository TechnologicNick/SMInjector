#pragma once

#include "Types.hpp"
#include "GameStartupParams.hpp"

namespace SM {
	class Contraption {
    public:
        virtual void vftable_0x00() = 0;
        virtual void vftable_0x08() = 0;
        virtual void vftable_0x10() = 0;
        virtual void vftable_0x18() = 0;
        virtual void vftable_0x20() = 0;
        virtual void vftable_0x28() = 0;
    public:
        std::shared_ptr<void*> m_pGuiSystemManager;
        std::shared_ptr<void*> m_pCommonGuiAdditions;
        std::shared_ptr<void*> m_pToolTipGui;
    private:
        void* field7_0x38;
        void* field8_0x40;
    public:
        std::shared_ptr<void*> m_pDirectoryManager;
        std::shared_ptr<void*> m_pConsole;
    public:
        uint32_t m_uScreenTargetX;
        uint32_t m_uScreenTargetY;
        uint32_t m_uScreenCurrentX;
        uint32_t m_uScreenCurrentY;
        GameStartupParams m_pGameStartupParams;
        std::vector<std::shared_ptr<void*>> m_pGameStates;
        bool m_bIsLoading;
    private:
        undefined field20_0x179;
        undefined field21_0x17a;
        undefined field22_0x17b;
    public:
        int m_uGameStateIndex;
        std::shared_ptr<void*> m_pTaskManager;
        std::shared_ptr<void*> m_pGameSettings;
        std::shared_ptr<void*> m_pDisplayOptions;
        std::shared_ptr<void*> m_pDebugManager;
        std::shared_ptr<void*> m_pSteamWorkshopManager;
        void* m_pSteamItemInventory;
        std::shared_ptr<void*> m_pUgcManager;
        std::shared_ptr<void*> m_pPopUpManager;
        void* m_pLoadingScreen;
        std::shared_ptr<void*> m_pProgressionManager;
        void* m_pCharacterCustomizationManager;
        std::shared_ptr<void*> m_pInputManager;
        std::shared_ptr<void*> m_pKeyBindings;
        void* m_pTemplateLoader;
        int m_iFOV;
        int m_iDisplayMode;
        int m_iShadowQuality;
        int m_iShaderQuality;
        int m_iReflectionQuality;
        int m_iDrawDistance;
        int m_iSSAO;
        int m_iTextureFiltering;
        int m_iParticleQuality;
        bool m_bVerticalSync;
        bool m_bFXAA;
        bool m_bDOF;
        bool m_bBloom;
        bool m_bGodrays;
        bool m_bDynamicLights;
    private:
        undefined field63_0x26a;
        undefined field64_0x26b;
    public:
        int m_iBrightness;
        struct RenderStateManager* m_pRenderStateManager;
        struct ResourceManager* m_pResourceManager;
        std::shared_ptr<void*> m_pAudioManager;
        HWND m_hWnd;
    private:
        undefined2 field71_0x298;
        undefined field72_0x29a;
        undefined field73_0x29b;
        undefined field74_0x29c;
        undefined field75_0x29d;
        undefined field76_0x29e;
        undefined field77_0x29f;
        undefined** field78_0x2a0;
        undefined field79_0x2a8;
        undefined field80_0x2a9;
        undefined field81_0x2aa;
        undefined field82_0x2ab;
        undefined4 field83_0x2ac;
        undefined** field84_0x2b0;
        undefined field85_0x2b8;
        undefined field86_0x2b9;
        undefined field87_0x2ba;
        undefined field88_0x2bb;
        undefined4 field89_0x2bc;
	};

    namespace {
        constexpr size_t Contraption_size = sizeof(Contraption);
        static_assert(sizeof(Contraption) == 704, "Contraption wrong size");
    }
}
