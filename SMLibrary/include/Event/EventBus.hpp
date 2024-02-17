#pragma once

#include "../stdafx.h"

#include <unordered_map>
#include <functional>

namespace SMLibrary::Event {
	template<typename EventType>
	class EventBus
	{
	public:
		using EventHandler = std::function<void(const EventType&)>;

	private:
		std::vector<EventHandler> m_handlers = {};

	public:
		EventBus() = default;

		void RegisterHandler(const EventHandler& handler)
		{
			m_handlers.emplace_back(handler);
		}

		void UnregisterHandler(const EventHandler& handler)
		{
			m_handlers.erase(std::remove(m_handlers.begin(), m_handlers.end(), handler), m_handlers.end());
		}

		void Emit(const EventType& event)
		{
			for (const auto& handler : m_handlers)
			{
				handler(event);
			}
		}
	private:
		EventBus(const EventBus&) = delete;
		EventBus& operator=(const EventBus&) = delete;
	};

	template<typename EventType>
	_LIB_FUNCTION EventBus<EventType>* GetEventBus()
#ifndef _SM_LIBRARY_BUILD_PLUGIN
	{
		static EventBus<EventType>* eventBus = nullptr;
		if (!eventBus) {
			eventBus = new EventBus<EventType>();
		}

		return eventBus;
	}
#else
	;
#endif // _SM_LIBRARY_BUILD_PLUGIN
}