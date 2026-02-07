import 'package:flutter/material.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:shared_preferences/shared_preferences.dart';

part 'settings_repository.g.dart';

@riverpod
SettingsRepository settingsRepository(SettingsRepositoryRef ref) {
  throw UnimplementedError();
}

class SettingsRepository {
  final SharedPreferences _prefs;

  SettingsRepository(this._prefs);

  static const _themeKey = 'theme_mode';
  static const _localeKey = 'locale';
  static const _autoPlayKey = 'auto_play';

  ThemeMode getThemeMode() {
    final themeIndex = _prefs.getInt(_themeKey);
    if (themeIndex == null) return ThemeMode.system;
    return ThemeMode.values[themeIndex];
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    await _prefs.setInt(_themeKey, mode.index);
  }

  String? getLocale() {
    return _prefs.getString(_localeKey);
  }

  Future<void> setLocale(String localeCode) async {
    await _prefs.setString(_localeKey, localeCode);
  }

  bool getAutoPlay() {
    return _prefs.getBool(_autoPlayKey) ?? true; // Default to true
  }

  Future<void> setAutoPlay(bool value) async {
    await _prefs.setBool(_autoPlayKey, value);
  }
}
