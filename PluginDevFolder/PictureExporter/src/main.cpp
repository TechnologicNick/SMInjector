#define _SM_LIBRARY_BUILD_PLUGIN
#define _SM_PLUGIN_NAME PictureExporter

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

	DWORD64 compare_gamemode = sigScanner.scan("\x48\x83\xB8\x20\x03\x00\x00\x00\x0F\x85\x00\x00\x00\x00\x83\x3D\x00\x00\x00\x00\x00\x0F\x85", "xxxxxxxxxx????xx?????xx", 14);
	if (!compare_gamemode) {
		Console::log(Color::LightRed, "Unable to find PictureExporter gamemode comparison in memory");
		return PLUGIN_ERROR;
	}

	Console::log(Color::Aqua, "Found PictureExporter gamemode comparison at %p", compare_gamemode);

	LPVOID dst = (LPVOID)compare_gamemode;
	size_t len = 13;
	DWORD oldProtection;
	DWORD temp;

	// Allow modifications of the target function
	VirtualProtect(dst, len, PAGE_EXECUTE_READWRITE, &oldProtection);

	// Replace the cmp and jne instructions with NOP
	memset((void*)compare_gamemode, 0x90, len);

	// Restore protection
	VirtualProtect(dst, len, oldProtection, &temp);



	return PLUGIN_SUCCESSFULL;
}

LIB_RESULT PluginUnload() {
	Console::log(Color::Aqua, "Unloading plugin...");
	return PLUGIN_SUCCESSFULL;
}
