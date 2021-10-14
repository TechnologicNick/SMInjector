#define _SM_LIBRARY_BUILD_PLUGIN
#define _SM_PLUGIN_NAME CustomGarments

#include <sm_lib.h>
#include <sigscan.h>
#include <console.h>
using Console::Color;



void garmentCodeHook(UINT32 expected, UINT32 got) {

	Console::log(Color::LightPurple, "Incorrect garment code detected! (expected %u, got %u)", expected, got);

}

LIB_RESULT PluginLoad() {
	Console::log(Color::Aqua, "Scanning for signature");

	SignatureScanner sigScanner(L"ScrapMechanic.exe");
	if (sigScanner.readMemory()) {

		DWORD64 garmentCode = sigScanner.scan("\x8B\x43\x7C\x3B\xF0\x74\x1E", "xxxxxxx", 5);
		if (!garmentCode) {
			Console::log(Color::LightRed, "Unable to find garment code comparison in memory");
			return PLUGIN_ERROR;
		}

		Console::log(Color::Aqua, "Found garment code comparison at %p", garmentCode);
		Console::log(Color::Aqua, "Installing hook to %p", &garmentCodeHook);


		// Replace instructions after the jump with NOP

		LPVOID dst = (LPVOID)(garmentCode + 2);
		size_t len = 30;
		DWORD oldProtection;
		DWORD temp;

		// Allow modifications of the target function
		VirtualProtect(dst, len, PAGE_EXECUTE_READWRITE, &oldProtection);

		// Fill with NOP
		memset(dst, 0x90, len);

		byte instructions[] = {
			0x8B, 0xD0, // mov	edi, eax	param1: got
			0x8B, 0xCE, // mov	exc, esi	param0: expected

			0xFF, 0x15, 0x02, 0x00, 0x00, 0x00, 0xEB, 0x08 // absolute call
		};

		memcpy(dst, instructions, sizeof(instructions));

		*(long long *)((long long)dst + sizeof(instructions)) = (long long)&garmentCodeHook;

		// Restore protection
		VirtualProtect(dst, len, oldProtection, &temp);

		Console::log(Color::Aqua, "Hook installed", &garmentCodeHook);
	}

	return PLUGIN_SUCCESSFULL;
}

LIB_RESULT PluginUnload() {
	Console::log(Color::Aqua, "Unloading this plugin!");
	return PLUGIN_SUCCESSFULL;
}