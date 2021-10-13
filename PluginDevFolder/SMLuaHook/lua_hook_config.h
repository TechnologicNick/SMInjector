#pragma once
#pragma warning(push)
#pragma warning(disable : 26819 28020)
#define JSON_DIAGNOSTICS 1
#include <nlohmann/json.hpp>
#pragma warning(pop)
#include <any>
#include <vector>
#include <set>
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>

#include "config.h"

namespace fs = std::filesystem;

using json = nlohmann::json;

namespace LuaHook {

	struct selector;
	struct executor;
	struct hookItem;

	typedef std::function<bool(std::map<std::string, std::any>& fields, hookItem& hookItem, selector& selector)> selectorFunction;
	typedef std::function<std::string(std::string* input, std::map<std::string, std::any>& fields, hookItem& hookItem, executor& executor)> executorFunction;

	struct selector {
		selectorFunction* func;

		json j_selector;
	};

	struct executor {
		executorFunction* func;

		json j_executor;
	};
	
	struct hookItem {
		float priority = 1;
		std::vector<selector> selector;
		std::vector<executor> execute;

		json j_hook;

		bool operator<(const hookItem& other) const {
			return this->priority < other.priority;
		}
	};

	namespace SelectorHelper {

		std::any getInput(std::map<std::string, std::any>& fields, hookItem& hookItem, selector& selector) {
			if (selector.j_selector.contains("field")) {
				std::string fieldName = selector.j_selector.at("field");

				if (fields.find(fieldName) == fields.end()) {
					throw new std::invalid_argument("Field not found");
				}

				return fields[fieldName];
			}
			else {
				if (fields.size() == 1) {
					return fields.begin()->second;
				}
				else {
					// Throw an exception
					selector.j_selector.at("field");
					return NULL;
				}
			}
		}

		std::string getInputConstCharPtr(std::map<std::string, std::any>& fields, hookItem& hookItem, selector& selector) {
			std::any input = SelectorHelper::getInput(fields, hookItem, selector);

			if (const char*** str = std::any_cast<const char**>(&input)) {
				return std::string(**str);
			}
			else {
				throw new std::invalid_argument(std::string("Field type not castable to const char**: ") + input.type().name());
			}
		}

	}
	
	std::map<std::string, selectorFunction> selectorFunctions = {
		{
			"CONTAINS", [](std::map<std::string, std::any>& fields, hookItem& hookItem, selector& selector) {
				std::string input = SelectorHelper::getInputConstCharPtr(fields, hookItem, selector);
				
				std::string value = selector.j_selector.at("value");

				return input.find(value) != std::string::npos;
			}
		},
		{
			"EQUALS", [](std::map<std::string, std::any>& fields, hookItem& hookItem, selector& selector) {
				std::string input = SelectorHelper::getInputConstCharPtr(fields, hookItem, selector);

				std::string value = selector.j_selector.at("value");

				return input.compare(value) == 0;
			}
		}
	};



	namespace ExecutorHelper {

		std::string readFile(fs::path path) {
			std::ifstream in(path);

			if (in.fail()) {
#pragma warning(suppress : 4996)
				throw std::exception((std::string() + "Failed to open file \"" + path.string() + "\": " + strerror(errno)).c_str());
			}

			std::ostringstream sstr;
			sstr << in.rdbuf();
			return sstr.str();
		}

	}

	std::map<std::string, executorFunction> executorFunctions = {
		{
			"REPLACE_CONTENT_WITH_FILE", [](std::string* input, std::map<std::string, std::any>& fields, hookItem& hookItem, executor& executor) {
				return input->assign(LuaHook::ExecutorHelper::readFile(PathHelper::resolvePath(executor.j_executor.at("file"))));
			}
		},
		{
			"PREPEND_FILE", [](std::string* input, std::map<std::string, std::any>& fields, hookItem& hookItem, executor& executor) {
				return input->insert(0, LuaHook::ExecutorHelper::readFile(PathHelper::resolvePath(executor.j_executor.at("file"))).append("\n"));
			}
		},
		{
			"APPEND_FILE", [](std::string* input, std::map<std::string, std::any>& fields, hookItem& hookItem, executor& executor) {
				return input->append("\n").append(LuaHook::ExecutorHelper::readFile(PathHelper::resolvePath(executor.j_executor.at("file"))));
			}
		},
		{
			"PREPEND_STRING", [](std::string* input, std::map<std::string, std::any>& fields, hookItem& hookItem, executor& executor) {
				return input->insert(0, executor.j_executor.at("string").get<std::string>().append("\n"));
			}
		},
		{
			"APPEND_STRING", [](std::string* input, std::map<std::string, std::any>& fields, hookItem& hookItem, executor& executor) {
				return input->append("\n").append(executor.j_executor.at("string"));
			}
		}
	};



	void from_json(const json& j, selector& s) {
		std::string op = j.at("operator").get<std::string>();

		if (selectorFunctions.find(op) == selectorFunctions.end()) {
			std::vector<std::string> opList;
			for (auto const& opFunc : selectorFunctions) {
				opList.push_back(opFunc.first);
			}

			throw std::exception((std::string() + "Unknown operator \"" + op + "\". Possible operators: " + json(opList).dump()).c_str());
		}

		s.func = &selectorFunctions.at(op);

		j.get_to(s.j_selector);
	}

	void from_json(const json& j, executor& e) {
		std::string command = j.at("command").get<std::string>();

		if (executorFunctions.find(command) == executorFunctions.end()) {
			std::vector<std::string> commandList;
			for (auto const& cmdFunc : executorFunctions) {
				commandList.push_back(cmdFunc.first);
			}

			throw std::exception((std::string() + "Unknown command \"" + command + "\". Possible commands: " + json(commandList).dump()).c_str());
		}

		e.func = &executorFunctions.at(command);

		j.get_to(e.j_executor);
	}

	void from_json(const json& j, hookItem& hi) {
		j.at("priority").get_to(hi.priority);
		j.at("selector").get_to(hi.selector);
		j.at("execute").get_to(hi.execute);

		j.get_to(hi.j_hook);
	}



	class HookConfig {
	public:
		inline static std::vector<HookConfig*> enabledConfigs;

	private:
		json root;
		std::map<std::string, std::vector<hookItem>> hooks;
		bool enabled = false;

	public:
		HookConfig(json root) {
			this->root = root;

			for (auto& [key, value] : this->root.at("hooks").items()) {
				try {
					this->hooks[key] = value.get<std::vector<hookItem>>();
				}
				catch (json::exception e) {
					Console::log(Color::LightRed, "Failed parsing %s hooks: %s", key.c_str(), e.what());
				}
				catch (std::exception e) {
					Console::log(Color::LightRed, "Failed processing %s hooks: %s", key.c_str(), e.what());
				}
			}
		}

		~HookConfig() {
			if (this->enabled) {
				Console::log(Color::LightYellow, "Warning: Deconstructing HookConfig while enabled!");
			}
		}

		void setEnabled(bool enabled) {
			if (enabled == this->enabled) {
				return;
			}

			if (enabled) {
				// Add this
				HookConfig::enabledConfigs.push_back(this);
			}
			else {
				// Remove this
				HookConfig::enabledConfigs.erase(std::remove(HookConfig::enabledConfigs.begin(), HookConfig::enabledConfigs.end(), this), HookConfig::enabledConfigs.end());
			}
		}

		static std::vector<hookItem> getHookItems(std::string name) {
			size_t totalSize = 0;

			// Calculate the total size
			for (auto& hookConfig : HookConfig::enabledConfigs) {
				if (hookConfig->hooks.find(name) == hookConfig->hooks.end())
					continue;

				totalSize += hookConfig->hooks[name].size();
			}

			std::vector<hookItem> items;
			items.reserve(totalSize);

			// Insert all hookItems into items
			for (auto& hookConfig : HookConfig::enabledConfigs) {
				if (hookConfig->hooks.find(name) == hookConfig->hooks.end())
					continue;

				items.insert(items.end(), hookConfig->hooks[name].begin(), hookConfig->hooks[name].end());
			}

			std::sort(items.begin(), items.end());

			return items;
		}

		static std::set<std::string> getHookNames() {
			std::set<std::string> names;

			// Insert all hookItems into items
			for (auto& hookConfig : HookConfig::enabledConfigs) {
				for (auto& [hookName, hookItems] : hookConfig->hooks) {
					names.insert(hookName);
				}
			}

			return names;
		}

	};



	size_t runLuaHook(std::string name, std::string* input, std::map<std::string, std::any>& fields) {
		size_t executeCount = 0;

		for (hookItem& hookItem : HookConfig::getHookItems(name)) {
			bool selected = true;

			for (selector& selector : hookItem.selector) {
				selected &= (*selector.func)(fields, hookItem, selector);

				DEBUG_LOG(selected ? Color::LightPurple : Color::Purple, selected ? "selected" : "not selected");

				if (!selected) {
					break;
				}
			}

			if (selected) {

				for (executor& executor : hookItem.execute) {
					try {
						(*executor.func)(input, fields, hookItem, executor);

						executeCount++;
					}
					catch (std::exception& e) {
						Console::log(Color::LightRed, "Failed executing executor %s: %s", executor.j_executor.dump(4).c_str(), e.what());
					}
				}

			}
		}

		return executeCount;
	}

}