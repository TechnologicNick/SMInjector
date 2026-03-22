#include "../include/stdafx.h"

#include <process.h>
#include <windows.h>
#include <stdio.h>
#include <vector>
#include <filesystem>
#include <system_error>

namespace fs = std::filesystem;

#define _SM_PLUGIN_NAME SMLibrary
#define _SM_OUTPUT_LOGS

#include "../include/sm_lib.h"
#include "../include/plugin_config.h"

#include "../include/console.h"
using Console::Color;

#include "../include/gamehook.h"
#include "../include/sigscan.h"

#include "hooks.h"

namespace SMLibrary {
	using namespace SMLibrary::Event;

	fs::path GetDllPath(HMODULE hModule) {
		TCHAR dllPath[MAX_PATH] = { 0 };
		DWORD length = GetModuleFileName(hModule, dllPath, _countof(dllPath));
		return fs::path(dllPath);
	}

	bool AllocConsoleNow() {
		if (!AllocConsole()) {
			MessageBox(NULL, TEXT("[SMInjector] Unable to allocate debug console"), TEXT("Error"), MB_OK | MB_ICONERROR);
			return false;
		}

		SetConsoleTitle(TEXT("Debug Console"));
		SetConsoleScreenBufferSize(stdout, { 0x100, 0x100 });
		SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), FOREGROUND_GREEN | FOREGROUND_BLUE | FOREGROUND_RED);

		if (!SetConsoleOutputCP(CP_UTF8)) {
			MessageBox(NULL, TEXT("[SMInjector] Unable to set console output codepage to UTF-8"), TEXT("Error"), MB_OK | MB_ICONERROR);
		}

		return true;
	}

	void PreventConsoleRealloc() {
		Hooks::pHookAllocConsole = GameHooks::InjectFromName("kernel32.dll", "AllocConsole", Hooks::Hook_ReturnTrue, 6);
	}

	void SetupDllDirectories(const fs::path& pDllPath) {
		fs::path baseDir = pDllPath.parent_path();

		fs::path directories[] = {
			baseDir,
			baseDir / "plugins",
			baseDir / "plugins" / "dependencies"
		};

		for (const fs::path& dir : directories) {
			if (!AddDllDirectory(dir.c_str())) {
				std::string body;
				body += "Failed adding dll directory \"";
				body += dir.string();
				body += "\"\nSome plugins might not load\n\nReason:\n";
				body += std::system_category().message(GetLastError());

				MessageBoxA(0, body.c_str(), "AddDllDirectory failed", MB_ICONERROR);
			}
		}

		if (!SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_DEFAULT_DIRS)) {
			std::string body;
			body += "Some plugins might not load\n\nReason:\n";
			body += std::system_category().message(GetLastError());

			MessageBoxA(0, body.c_str(), "SetDefaultDllDirectories failed", MB_ICONERROR);
		}
	}

	void OnInject(const fs::path& pDllPath) {
		// Allocate the console before the game does
		if (AllocConsoleNow()) {
			Console::log_open();
			Console::log(Color::Aqua, "Allocated console");
			PreventConsoleRealloc();
		}

		SetupDllDirectories(pDllPath);

		PluginConfig::setConfigDirectory(pDllPath.parent_path() / "config");

		if (!Hooks::InstallHooks()) {
			Console::log(Color::LightRed, "Failed to install hooks");
			return;
		}
	}
}


BOOL WINAPI DllMain(HMODULE hModule, DWORD fdwReason, LPVOID lpReserved) {
	switch(fdwReason)  { 
		case DLL_PROCESS_ATTACH:
			MessageBox(0, L"From DLL\n", L"Process Attach", MB_ICONINFORMATION);

			SMLibrary::OnInject(SMLibrary::GetDllPath(hModule));
			break;

		case DLL_PROCESS_DETACH:
			break;

		case DLL_THREAD_ATTACH:
			break;

		case DLL_THREAD_DETACH:
			break;
	}

	return TRUE;
}
