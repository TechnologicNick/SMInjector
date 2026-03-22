#pragma once

#include "Event.hpp"
#include "EventBus.hpp"

namespace SMLibrary::Event {
	struct ProcessStartEvent : Event {
	};

	template _LIB_FUNCTION EventBus<ProcessStartEvent>* GetEventBus();
}
