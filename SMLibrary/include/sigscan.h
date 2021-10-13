#pragma once

#include <windows.h>
#include <tlhelp32.h>
#include <tchar.h>
#include <Psapi.h>

#include "console.h"

#define ERROR_GETMODULE(reason, ...) Console::log(Color::LightRed, "[SignatureScanner] Failed getting handle of module %s. Reason: " reason, moduleName, __VA_ARGS__)

using Console::Color;

class SignatureScanner {
private:
	LPCWSTR moduleName;
	DWORD64 moduleBase;
	DWORD moduleSize;
	HMODULE moduleHandle;

	MODULEINFO GetModuleInfo(LPCWSTR moduleName) {
		MODULEINFO moduleInfo = { 0 };
		this->moduleHandle = GetModuleHandle(moduleName);
		if (this->moduleHandle == NULL)
			return moduleInfo;

		GetModuleInformation(GetCurrentProcess(), this->moduleHandle, &moduleInfo, sizeof(MODULEINFO));

		return moduleInfo;
	}

	BYTE* data;

public:
	SignatureScanner(LPCWSTR moduleName) {
		this->moduleName = moduleName;

		MODULEINFO moduleInfo = GetModuleInfo(moduleName);

		if (moduleInfo.SizeOfImage == 0) {
			Console::log(Color::LightRed, "[SignatureScanner] Failed getting info of module %s", moduleName);
			return;
		}

		this->moduleBase = (DWORD64) moduleInfo.lpBaseOfDll;
		this->moduleSize = moduleInfo.SizeOfImage;

		Console::wlog(Color::Aqua, L"[SignatureScanner] Found module %s with base=[0x%llX] size=[%lu]", moduleName, this->moduleBase, this->moduleSize);
	}

	~SignatureScanner() {
		delete[] data;
	}

	bool readMemory() {
		data = new BYTE[this->moduleSize];

		if (!ReadProcessMemory(GetCurrentProcess(), (LPCVOID)this->moduleBase, this->data, this->moduleSize, NULL)) {
#pragma warning(suppress : 4996)
			Console::log(Color::LightRed, "[SignatureScanner] Failed reading process memory: %s", strerror(errno));
			return false;
		}

		return true;
	}

	DWORD64 scan(const char* signature, const char* mask, DWORD64 offset) {
		size_t length = strlen(mask);

		for (DWORD64 i = 0; i < this->moduleSize - length - 1; i++) {

			bool found = true;

			for (size_t j = 0; j < length; j++) {
				found &= mask[j] == '?' || signature[j] == *(char*)(this->moduleBase + i + j);
			}

			if (found) {
				return this->moduleBase + i + offset;
			}
		}

		return NULL;
	}

	DWORD64 scan(const char* signature, const char* mask) {
		return this->scan(signature, mask, 0);
	}

};

#undef ERROR_GETMODULE
