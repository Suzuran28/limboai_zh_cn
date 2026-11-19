/**
 * translation.h
 * =============================================================================
 * Copyright (c) 2023-present Serhii Snitsaruk and the LimboAI contributors.
 *
 * Use of this source code is governed by an MIT-style
 * license that can be found in the LICENSE file or at
 * https://opensource.org/licenses/MIT.
 * =============================================================================
 */
#ifndef COMPAT_TRANSLATION_H
#define COMPAT_TRANSLATION_H

#ifdef LIMBOAI_MODULE
#include <core/string/ustring.h>
#endif // LIMBOAI_MODULE

#ifdef LIMBOAI_GDEXTENSION
#include <godot_cpp/variant/string.hpp>

using namespace godot;

// Editor-facing translation. Looks up the bundled "limboai" translation domain so
// the editor UI can be localized independently from the project's own translations
// (the main translation domain is disabled by the editor while plugins are created).
String TTR(const String &p_text, const String &p_context = "");

// Runtime-facing translation. Uses the project's translations (main domain) so that
// console messages and runtime strings respect the language of the running game.
String RTR(const String &p_text, const String &p_context = "");

// Loads the translation catalogs shipped in res://addons/limboai/translations/ into
// the "limboai" translation domain. Project translations are registered as overrides.
void limboai_load_editor_translations();

#endif // LIMBOAI_GDEXTENSION

#endif // COMPAT_TRANSLATION_H
