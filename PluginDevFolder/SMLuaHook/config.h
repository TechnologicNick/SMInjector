#pragma once
#pragma warning(push)
#pragma warning(disable : 26819 28020)
#define JSON_DIAGNOSTICS 1
#include <nlohmann/json.hpp>
#pragma warning(pop)
#include <plugin_config.h>
#include <console.h>

using Console::Color;

#define CONFIG_FIELD(field) Config::##field = config.root.value(#field, Config::##field);

namespace LuaHook {

	namespace Config {
		static bool lua_debug = false;

		namespace {
			const char* defaultContent = R"(// Main configuration file for SMLuaHook
{
	// Log various lua things useful for making hooks
	"lua_debug": false
}
)";
		}

		void load() {
			Console::log(Color::Aqua, "Loading config.json...");

			try {
				PluginConfig config(_LIB_PLUGIN_NAME_STR, "config.json");
				config.setDefaultContent(defaultContent);
				config.createIfNotExists();
				config.load();

				CONFIG_FIELD(lua_debug)

				Console::log(Color::Aqua, "Loaded config.json");
			}
			catch (std::exception e) {
				Console::log(Color::Red, "Failed loading config.json: %s", e.what());
			}
		}
	}

}

#define DEBUG_LOG(...) if (LuaHook::Config::lua_debug) Console::log(__VA_ARGS__)
