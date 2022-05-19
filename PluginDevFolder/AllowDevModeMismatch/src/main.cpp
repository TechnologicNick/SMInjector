#define _SM_LIBRARY_BUILD_PLUGIN
#define _SM_PLUGIN_NAME AllowDevModeMismatch

#include <sm_lib.h>
#include <console.h>
#include <sigscan.h>
using Console::Color;

LIB_RESULT PluginLoad() {
	Console::log(Color::Aqua, "Starting plugin...");



	SignatureScanner sigScanner(L"ScrapMechanic.exe");
	if (!sigScanner.readMemory()) {
		Console::log(Color::LightRed, "Failed to read the memory of ScrapMechanic.exe");
		return false;
	}

	DWORD64 compare_flag = sigScanner.scan("\x38\x43\x78\x0F\x85", "xxxxx");
	if (!compare_flag) {
		Console::log(Color::LightRed, "Unable to find developer mode flag comparison in memory");
		return PLUGIN_ERROR;
	}

	Console::log(Color::Aqua, "Found developer mode flag comparison at %p", compare_flag);

	LPVOID dst = (LPVOID)compare_flag;
	size_t len = 9;
	DWORD oldProtection;
	DWORD temp;

	// Allow modifications of the target function
	VirtualProtect(dst, len, PAGE_EXECUTE_READWRITE, &oldProtection);

	// Replace the cmp and jne instructions with NOP
	memset((void*)compare_flag, 0x90, len);

	// Restore protection
	VirtualProtect(dst, len, oldProtection, &temp);



	return PLUGIN_SUCCESSFULL;
}

LIB_RESULT PluginUnload() {
	Console::log(Color::Aqua, "Unloading plugin...");
	return PLUGIN_SUCCESSFULL;
}
