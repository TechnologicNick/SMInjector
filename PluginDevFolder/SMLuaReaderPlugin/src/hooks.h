#pragma once
#include <stdio.h>
#include <gamehook.h>
#include <lua.hpp>

#include <console.h>
using Console::Color;


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

namespace Hooks {
	void hook_luaL_register(lua_State* L, const char* libname, const luaL_Reg* l) {
		Console::log(Color::Aqua, "hook_luaL_register: libname=[%s]", libname);

		const luaL_Reg* ptr = l;

		for (int i = 0; ptr && ptr->name != NULL; i++, ptr++) {
			Console::log(Color::Aqua, "hook_luaL_register: luaL_Reg[%d] name=[%s] func=[%p]", i, ptr->name, (void*)ptr->func);
		}

		return ((pluaL_register)*hck_luaL_register)(L, libname, l);
	}

	int hook_luaL_loadstring(lua_State* L, const char* s) {
		Console::log(Color::Aqua, "hook_luaL_loadstring: s=[ ... ]");
		return ((pluaL_loadstring)*hck_luaL_loadstring)(L, s);
	}

	lua_State* hook_lua_newstate(lua_Alloc f, void* ud) {
		Console::log(Color::Aqua, "hck_lua_newstate: ud=[%p]", ud);
		return ((plua_newstate)*hck_lua_newstate)(f, ud);
	}

	int hook_luaL_loadbuffer(lua_State* L, const char* buff, size_t sz, const char* name) {
		Console::log(Color::Aqua, "hck_luaL_loadbuffer: buff=[ ... ], sz=[%zu], name=[%s]", sz, name);
		return ((pluaL_loadbuffer)*hck_luaL_loadbuffer)(L, buff, sz, name);
	}
}
