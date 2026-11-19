/**
 * translation.cpp
 * =============================================================================
 * Copyright (c) 2023-present Serhii Snitsaruk and the LimboAI contributors.
 *
 * Use of this source code is governed by an MIT-style
 * license that can be found in the LICENSE file or at
 * https://opensource.org/licenses/MIT.
 * =============================================================================
 */
#include "translation.h"

#ifdef LIMBOAI_GDEXTENSION

#include "project_settings.h"

#include <godot_cpp/classes/dir_access.hpp>
#include <godot_cpp/classes/engine.hpp>
#include <godot_cpp/classes/file_access.hpp>
#include <godot_cpp/classes/project_settings.hpp>
#include <godot_cpp/classes/resource_loader.hpp>
#include <godot_cpp/classes/translation.hpp>
#include <godot_cpp/classes/translation_domain.hpp>
#include <godot_cpp/classes/translation_server.hpp>
#include <godot_cpp/core/print_string.hpp>
#include <godot_cpp/core/property_info.hpp>
#include <godot_cpp/variant/dictionary.hpp>
#include <godot_cpp/variant/packed_string_array.hpp>
#include <godot_cpp/variant/typed_array.hpp>
#include <godot_cpp/templates/vector.hpp>

namespace {

// Name of the dedicated translation domain used by the LimboAI editor UI.
const char *LIMBOAI_DOMAIN = "limboai";
// Catalogs shipped with the addon (generated from i18n/ui/*.po).
const char *LIMBOAI_TRANSLATIONS_DIR = "res://addons/limboai/translations";
// Optional per-project override: empty means "follow the editor language".
const char *LIMBOAI_LANGUAGE_SETTING = "limbo_ai/editor/language";

bool _has_translation_domains() {
	// TranslationDomain was added in Godot 4.4.
	static const bool supported = []() {
		const Engine *engine = Engine::get_singleton();
		if (engine == nullptr) {
			return false;
		}
		const Dictionary version = engine->get_version_info();
		const int major = int(version.get("major", 0));
		const int minor = int(version.get("minor", 0));
		return major > 4 || (major == 4 && minor >= 4);
	}();
	return supported;
}

// PO catalogs are plain text, so the addon can ship them without relying on the
// editor's import step (which would leave the UI untranslated on first launch).

String _unescape_po(const String &p_text) {
	String out;
	for (int i = 0; i < p_text.length(); i++) {
		const char32_t c = p_text[i];
		if (c == '\\' && i + 1 < p_text.length()) {
			const char32_t next = p_text[i + 1];
			switch (next) {
				case 'n':
					out += '\n';
					break;
				case 't':
					out += '\t';
					break;
				case 'r':
					out += '\r';
					break;
				default:
					out += next;
					break;
			}
			i++;
		} else {
			out += c;
		}
	}
	return out;
}

String _parse_po_quoted(const String &p_line) {
	const int start = p_line.find("\"");
	const int end = p_line.rfind("\"");
	if (start < 0 || end <= start) {
		return String();
	}
	return _unescape_po(p_line.substr(start + 1, end - start - 1));
}

void _load_po_catalog(const String &p_path, const Ref<TranslationDomain> &p_domain) {
	const String text = FileAccess::get_file_as_string(p_path);
	if (text.is_empty()) {
		return;
	}

	Vector<String> msgids;
	Vector<String> msgstrs;
	String locale;
	String msgid;
	String msgstr;
	bool in_msgid = false;
	bool in_msgstr = false;
	bool first_entry = true;

	auto flush_entry = [&]() {
		if (msgid.is_empty()) {
			if (first_entry) {
				// Header entry: pull the locale out of the "Language:" field.
				for (const String &row : msgstr.split("\n")) {
					const String line = row.strip_edges();
					if (line.begins_with("Language:")) {
						locale = line.substr(String("Language:").length()).strip_edges();
						break;
					}
				}
			}
		} else if (!msgstr.is_empty()) {
			msgids.push_back(msgid);
			msgstrs.push_back(msgstr);
		}
		msgid = String();
		msgstr = String();
		in_msgid = false;
		in_msgstr = false;
		first_entry = false;
	};

	const PackedStringArray lines = text.split("\n");
	for (int i = 0; i < lines.size(); i++) {
		const String line = lines[i].strip_edges();
		if (line.is_empty() || line.begins_with("#")) {
			continue;
		}
		if (line.begins_with("msgid ")) {
			flush_entry();
			in_msgid = true;
			msgid = _parse_po_quoted(line.substr(6));
		} else if (line.begins_with("msgstr ")) {
			in_msgstr = true;
			msgstr = _parse_po_quoted(line.substr(7));
		} else if (line.begins_with("\"")) {
			if (in_msgid) {
				msgid += _parse_po_quoted(line);
			} else if (in_msgstr) {
				msgstr += _parse_po_quoted(line);
			}
		}
	}
	flush_entry();

	if (msgids.is_empty()) {
		return;
	}
	if (locale.is_empty()) {
		// Fall back to the locale embedded in the file name: "limboai.zh_CN.po".
		locale = p_path.get_file().get_basename().get_extension();
	}
	if (locale.is_empty()) {
		return;
	}

	Ref<Translation> translation;
	translation.instantiate();
	translation->set_locale(locale);
	for (int i = 0; i < msgids.size(); i++) {
		translation->add_message(msgids[i], msgstrs[i]);
	}
	p_domain->add_translation(translation);
	print_verbose(vformat("LimboAI: loaded %d translation messages from %s (locale: %s).", msgids.size(), p_path, locale));
}

} // namespace

String TTR(const String &p_text, const String &p_context) {
	TranslationServer *server = TranslationServer::get_singleton();
	if (server == nullptr) {
		return p_text;
	}

	if (!_has_translation_domains()) {
		// Older engines: fall back to the main domain (same behavior as before).
		return server->translate(p_text, p_context);
	}

	const Ref<TranslationDomain> domain = server->get_or_add_domain(LIMBOAI_DOMAIN);
	if (domain.is_null()) {
		return p_text;
	}
	return domain->translate(p_text, p_context);
}

String RTR(const String &p_text, const String &p_context) {
	const TranslationServer *server = TranslationServer::get_singleton();
	if (server == nullptr) {
		return p_text;
	}
	return String(server->translate(p_text, p_context));
}

void limboai_load_editor_translations() {
	TranslationServer *server = TranslationServer::get_singleton();
	if (server == nullptr || !_has_translation_domains()) {
		return;
	}

	const Ref<TranslationDomain> domain = server->get_or_add_domain(LIMBOAI_DOMAIN);
	if (domain.is_null()) {
		return;
	}

	// Register the optional language override, so a user can force e.g. zh_CN
	// while keeping the editor itself in English.
	GLOBAL_DEF(PropertyInfo(Variant::STRING, LIMBOAI_LANGUAGE_SETTING, PROPERTY_HINT_LOCALE_ID, ""), "");
	const String language_override = GLOBAL_GET(LIMBOAI_LANGUAGE_SETTING);
	if (!language_override.is_empty()) {
		domain->set_locale_override(language_override);
	}

	// Project-level catalogs act as user-provided overrides/additions.
	const TypedArray<Ref<Translation>> project_translations = server->get_translations();
	for (int i = 0; i < project_translations.size(); i++) {
		const Ref<Translation> translation = project_translations[i];
		if (translation.is_valid()) {
			domain->add_translation(translation);
		}
	}

	// Catalogs bundled with the addon.
	const PackedStringArray files = DirAccess::get_files_at(LIMBOAI_TRANSLATIONS_DIR);
	bool has_po = false;
	for (int i = 0; i < files.size(); i++) {
		if (files[i].ends_with(".po")) {
			has_po = true;
			break;
		}
	}
	for (int i = 0; i < files.size(); i++) {
		const String file = files[i];
		const String path = String(LIMBOAI_TRANSLATIONS_DIR).path_join(file);
		if (has_po) {
			if (file.ends_with(".po")) {
				_load_po_catalog(path, domain);
			}
		} else if (file.ends_with(".translation")) {
			const Ref<Translation> translation = ResourceLoader::get_singleton()->load(path);
			if (translation.is_valid()) {
				domain->add_translation(translation);
			}
		}
	}
}

#endif // LIMBOAI_GDEXTENSION
