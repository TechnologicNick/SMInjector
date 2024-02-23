#pragma once

#include "Event.hpp"
#include "EventBus.hpp"

namespace SMLibrary::Event {
	struct SteamInitializedEvent : Event {
	};

	template _LIB_FUNCTION EventBus<SteamInitializedEvent>* GetEventBus();
}
