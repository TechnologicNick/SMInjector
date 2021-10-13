#define _SM_LIBRARY_BUILD_PLUGIN
#define _SM_PLUGIN_NAME SMLuaHook

#include <sm_lib.h>
#include <console.h>
#include <sigscan.h>
#include <plugin_config.h>

using Console::Color;

#include "config.h"
#include "hooks.h"
#include "lua_hook_config.h"
bool InjectLua();

LIB_RESULT PluginLoad() {
	Console::log(Color::Aqua, "Starting plugin ...");

	LuaHook::Config::load();

	if (!InjectLua()) {
		Console::log(Color::Red, "Failed to inject lua functions");
		return PLUGIN_ERROR;
	}

	return PLUGIN_SUCCESSFULL;
}

const char* defaultConfig = R"(// Configuration file for hooking the Lua C API
{
	"hooks": {

		// This function is used for setting up the Lua environment
		"luaL_loadstring": [
			/*
			{
				// Replace the environment table (the functions accessible inside
				// the lua sandbox) with an environment table loaded from a file
				
				// Hooks are ran from high to low priority
				"priority": 1,
				
				// All selectors must result in true for commands to be ran
				"selector": [
					{
						// The "name" field can be omitted if the hooked function has
						// at most one string field (check the (Lua/Luajit) source code)

						// "name": "s",
						"operator": "CONTAINS",
						"value": "unsafe_env"
					}
				],

				"execute": [
					{
						"command": "REPLACE_CONTENT_WITH_FILE",
						"file": "$PLUGIN_CONFIG/override/unsafe_env.lua"
					}
				]
			}
			*/
		],

		// All files the game tries to load pass through here
		"luaL_loadbuffer": [
			/*
			{
				// Enable survival dev mode

				"priority": 1,
				"selector": [
					{
				    	"field": "name",
				    	"operator": "EQUALS",
				    	"value": "Survival/Scripts/game/SurvivalGame.lua"
					}
				],
				"execute": [
					{
						"command": "PREPEND_STRING",
						"string": "g_survivalDev = true"
					}
				]
			}
			*/
		]
		
	}
}
)";

bool InjectLua() {
	Console::log(Color::Aqua, "Installing lua hooks");

	hck_luaL_register = GameHooks::InjectFromName("lua51.dll", "luaL_register", &LuaHook::Hooks::hook_luaL_register, 15);
	hck_luaL_loadstring = GameHooks::InjectFromName("lua51.dll", "luaL_loadstring", &LuaHook::Hooks::hook_luaL_loadstring, 16);
	hck_lua_newstate = GameHooks::InjectFromName("lua51.dll", "lua_newstate", &LuaHook::Hooks::hook_lua_newstate, 6);
	hck_luaL_loadbuffer = GameHooks::InjectFromName("lua51.dll", "luaL_loadbuffer", &LuaHook::Hooks::hook_luaL_loadbuffer, 13);

	if (!hck_luaL_register) {
		Console::log(Color::Red, "Failed to inject 'luaL_register'");
		return false;
	}

	if (!hck_luaL_loadstring) {
		Console::log(Color::Red, "Failed to inject 'luaL_loadstring'");
		return false;
	}

	if (!hck_lua_newstate) {
		Console::log(Color::Red, "Failed to inject 'lua_newstate'");
		return false;
	}

	if (!hck_luaL_loadbuffer) {
		Console::log(Color::Red, "Failed to inject 'luaL_loadbuffer'");
		return false;
	}

	PluginConfig config(_LIB_PLUGIN_NAME_STR, "lua_hooks.json");
	config.setDefaultContent(defaultConfig);
	config.createIfNotExists();
	config.load();

	try {
		Console::log(Color::Aqua, "Loading Lua C API hook config files...");
		LuaHook::HookConfig *hookConfig = new LuaHook::HookConfig(config.root);
		hookConfig->setEnabled(true);
	}
	catch (const json::exception& e) {
		Console::log(Color::LightRed, "Failed initialising HookConfig: %s", e.what());
	}

	Console::log(Color::Aqua, "Loaded %llu Lua C API hook config files", LuaHook::HookConfig::enabledConfigs.size());
	for (auto& hookName : LuaHook::HookConfig::getHookNames()) {
		Console::log(Color::Aqua, "    %s (%llu)", hookName.c_str(), LuaHook::HookConfig::getHookItems(hookName).size());
	}


	return true;
}

LIB_RESULT PluginUnload() {
	Console::log(Color::Aqua, "Unloading this plugin!");
	//util->Unload();
	return PLUGIN_SUCCESSFULL;
}
