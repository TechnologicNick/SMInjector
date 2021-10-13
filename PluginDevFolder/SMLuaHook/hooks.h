#pragma once
#include <stdio.h>
#include <gamehook.h>
#include <path_helper.h>
#include <lua.hpp>

#include <console.h>
using Console::Color;

#include "config.h"
#include "lua_hook_config.h"


// LUAL_REGISTER
typedef void (*pluaL_register)(lua_State*, const char*, const luaL_Reg*);
GameHook* hck_luaL_register;

// LUAL_LOADSTRING
typedef int (*pluaL_loadstring)(lua_State*, const char*);
GameHook* hck_luaL_loadstring;

// LUA_NEWSTATE
typedef lua_State* (*plua_newstate)(lua_Alloc, void*);
GameHook* hck_lua_newstate;

// LUAL_LOADBUFFER
typedef int (*pluaL_loadbuffer)(lua_State*, const char*, size_t, const char*);
GameHook* hck_luaL_loadbuffer;

// =============

namespace LuaHook::Hooks {
	void hook_luaL_register(lua_State* L, const char* libname, const luaL_Reg* l) {
		if (!LuaHook::Config::lua_debug) {
			return ((pluaL_register)*hck_luaL_register)(L, libname, l);
		}

		DEBUG_LOG(Color::Aqua, "hook_luaL_register: libname=[%s]", libname);

		const luaL_Reg* ptr = l;

		int i = 0;
		while (ptr->name != NULL) {
			DEBUG_LOG(Color::Aqua, "hook_luaL_register: luaL_Reg[%d] name=[%s] func=[%p]", i++, ptr->name, (void*)ptr->func);

			ptr++;
		}

		return ((pluaL_register)*hck_luaL_register)(L, libname, l);
	}

	int hook_luaL_loadstring(lua_State* L, const char* s) {
		DEBUG_LOG(Color::Aqua, "hook_luaL_loadstring: s=[ ... ]");

		std::map<std::string, std::any> fields = {
			{"s", &s}
		};

		std::string input(s);

		if (LuaHook::runLuaHook("luaL_loadstring", &input, fields)) {
			DEBUG_LOG(Color::Green, "Set contents to:\n%s", input.c_str());
			return ((pluaL_loadstring)*hck_luaL_loadstring)(L, input.c_str());
		}

		return ((pluaL_loadstring)*hck_luaL_loadstring)(L, s);
	}

	lua_State* hook_lua_newstate(lua_Alloc f, void* ud) {
		DEBUG_LOG(Color::Aqua, "hck_lua_newstate: ud=[%p]", ud);
		return ((plua_newstate)*hck_lua_newstate)(f, ud);
	}

	int hook_luaL_loadbuffer(lua_State* L, const char* buff, size_t sz, const char* name) {
		DEBUG_LOG(Color::Aqua, "hck_luaL_loadbuffer: buff=[ ... ], sz=[%zu], name=[%s]", sz, name);

		std::map<std::string, std::any> fields = {
			{"buff", &buff},
			{"name", &name}
		};

		std::string input(buff, sz);

		if (size_t executeCount = LuaHook::runLuaHook("luaL_loadbuffer", &input, fields)) {
			DEBUG_LOG(Color::Green, "Set contents to:\n%s", input.c_str());
			return ((pluaL_loadbuffer)*hck_luaL_loadbuffer)(L, input.c_str(), input.size(), name);
		}

		return ((pluaL_loadbuffer)*hck_luaL_loadbuffer)(L, buff, sz, name);
	}
}
