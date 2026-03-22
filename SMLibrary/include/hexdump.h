#pragma once
#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

std::string hexdump(const void* data, size_t size) {
    std::ostringstream result;
    const unsigned char* buffer = static_cast<const unsigned char*>(data);

    for (size_t i = 0; i < size; i += 16) {
        result << std::setfill('0') << std::setw(8) << std::hex << i << "  ";
        size_t j;
        for (j = 0; j < 16 && i + j < size; ++j) {
            result << std::setw(2) << static_cast<unsigned int>(buffer[i + j]) << ' ';
        }
        for (; j < 16; ++j) {
            result << "   ";
        }
        result << "|";
        for (j = 0; j < 16 && i + j < size; ++j) {
            char c = buffer[i + j];
            if (c >= 32 && c <= 126) {
                result << c;
            }
            else {
                result << '.';
            }
        }
        result << "|\n";
    }

    return result.str();
}
