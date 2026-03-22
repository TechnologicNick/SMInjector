#pragma once

#include "stdafx.h"

#include <windows.h>

#ifndef _SM_LIBRARY_ALLOW_OLD_HOOKS
#error \
The header file 'hook.h' is deprecated and will be removed in the future.\
To enable this header use '#define _SM_LIBRARY_ALLOW_OLD_HOOKS'\
This header will be removed in the future.
#else
#pragma message ("The header file 'hook.h' is deprecated and will be removed in the future.")
#endif

#include <string>
using std::string;

#include <map>
using std::map;


typedef unsigned char BYTE;
typedef long long longlong;

class _LIB_CLASS Hook {
	private:
		BYTE *gate = NULL;
		void *func = NULL;
		longlong last_pointer = 0;
		int length = 0;
		int offset = 0;
	public:
		~Hook();
		bool InjectFromName(const char *module_name, const char *proc_name, void *src, int len);
		bool InjectFromName(const char *module_name, const char *proc_name, void *src, int offset, int len);
		bool Inject(void *dst, void *src, int len);
		bool Inject(void *dst, void *src, int offset, int len);
		bool Uninject();
		void* Gate();
};

struct cmp_str {
	bool operator()(char const *a, char const *b) const {
		return std::strcmp(a, b) < 0;
	}
};

class HookUtility {
	private:
		map<const char*, map<const char*, Hook*, cmp_str>, cmp_str> injects;

	public:
		Hook *InjectFromName(const char *module_name, const char *proc_name, void *src, int offset, int len) {
			auto it = injects.find(module_name);
			if(it != injects.end()) { // We have the key
				auto& map = it->second;

				auto it2 = map.find(proc_name);
				if(it2 != map.end()) {
					//printf("This element already exists! module=[%s], proc=[%s]\n", module_name, proc_name);
					return NULL;
				}

				Hook *hook = new Hook();
				map[proc_name] = hook;
				hook->InjectFromName(module_name, proc_name, src, offset, len);
				return hook;
			} else {
				injects[module_name] = map<const char*, Hook*, cmp_str>();
				auto& map = injects[module_name];

				auto it2 = map.find(proc_name);
				if(it2 != map.end()) {
					//printf("This element already exists! module=[%s], proc=[%s]\n", module_name, proc_name);
					return NULL;
				}

				Hook *hook = new Hook();
				map[proc_name] = hook;
				hook->InjectFromName(module_name, proc_name, src, offset, len);
				return hook;
			}
		}

		Hook *InjectFromName(const char *module_name, const char *proc_name, void *src, int len) {
			return InjectFromName(module_name, proc_name, src, 0, len);
		}

		bool Unload() {
			auto it = injects.begin();

			for(; it != injects.end(); it++) {
				const char *module_name = it->first;

				map<const char*, Hook*, cmp_str>& map = it->second;
				auto it2 = map.begin();
				for(; it2 != map.end(); it2++) {
					const char *proc_name = it2->first;
					Hook *hook = it2->second;

					hook->Uninject();
					delete hook;
				}
			}

			injects.clear();
			return true;
		}
};
