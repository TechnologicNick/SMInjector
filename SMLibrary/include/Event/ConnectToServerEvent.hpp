#pragma once

#include "Event.hpp"
#include "EventBus.hpp"

namespace SMLibrary::Event {
	struct ConnectToServerEvent : Event {
		uint64_t uConnectSteamId;
		std::string sPassphrase;
	};

	template _LIB_FUNCTION EventBus<ConnectToServerEvent>* GetEventBus();
}
