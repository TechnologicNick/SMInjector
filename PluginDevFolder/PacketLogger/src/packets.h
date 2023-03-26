#pragma once

#include <cstdint>

enum Direction : uint8_t {
    ServerBound = 0,
    ClientBound = 1,
};

struct Packet {
	Direction direction;
	void* data;
	size_t size;
};
