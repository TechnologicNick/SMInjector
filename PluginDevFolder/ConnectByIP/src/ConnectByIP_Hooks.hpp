#pragma once

#include <Windows.h>
#include <type_traits>
#include <gamehook.h>

#include "steam.h"
#include <sdk/sm/ScrapMechanic.hpp>

#include <console.h>
using Console::Color;

namespace ConnectByIP::Hooks {

    bool InstallHooks() {
        Console::log(Color::Aqua, "Installing hooks...");

        Console::log(Color::Aqua, "g_contraption = %p", SM::g_contraption);

        Console::log(Color::Aqua, "Hooks installed!");
        return true;
    }

    bool UninstallHooks() {
        Console::log(Color::Aqua, "Hooks uninstalled!");
        return true;
    }
}
