#pragma once

#include "Event.hpp"
#include "EventBus.hpp"

namespace SMLibrary::Event {
	struct ProcessCreateEvent : Event {
	};

	template _LIB_FUNCTION EventBus<ProcessCreateEvent>& GetEventBus();
}
