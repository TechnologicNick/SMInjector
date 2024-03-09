#pragma once

// Ensure std::string is 32 bytes
#pragma push_macro("_ITERATOR_DEBUG_LEVEL")
#undef _ITERATOR_DEBUG_LEVEL
#define _ITERATOR_DEBUG_LEVEL 0
#define _ALLOW_ITERATOR_DEBUG_LEVEL_MISMATCH 1

#include <string>
#include <vector>

#pragma pop_macro("_ITERATOR_DEBUG_LEVEL")

#include <memory>

typedef unsigned char undefined;
typedef unsigned short undefined2;
typedef unsigned int undefined4;

// Hide from other files
namespace {
	constexpr size_t string_size = sizeof(std::string);
	static_assert(sizeof(std::string) == 32, "std::string wrong size");

	constexpr size_t vector_size = sizeof(std::vector<void*>);
	static_assert(sizeof(std::vector<int>) == 24, "std::vector<void*> wrong size");
}
