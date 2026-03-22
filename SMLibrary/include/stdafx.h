
#define _LIB_EXPORT_CLASS __declspec(dllexport)
#define _LIB_EXPORT __declspec(dllexport)

#define _LIB_IMPORT_CLASS __declspec(dllimport)
#define _LIB_IMPORT __declspec(dllimport)

#ifdef _SM_LIBRARY_BUILD_PLUGIN
	#define _LIB_CLASS _LIB_IMPORT_CLASS
	#define _LIB_FUNCTION _LIB_IMPORT
	#define _LIB_ENTRY __declspec(dllexport)
#else
	#define _LIB_CLASS _LIB_EXPORT_CLASS
	#define _LIB_FUNCTION _LIB_EXPORT
#endif

#define PLUGIN_SUCCESSFULL 1
#define PLUGIN_ERROR 0

#include "sdk/sm/Types.hpp"