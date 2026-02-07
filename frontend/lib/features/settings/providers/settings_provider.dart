import 'package:flutter/material.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:astro_guide/features/settings/data/settings_repository.dart';

part 'settings_provider.g.dart';

@riverpod
class Settings extends _$Settings {
  @override
  SettingsState build() {
    final repository = ref.watch(settingsRepositoryProvider);
    return SettingsState(
      themeMode: repository.getThemeMode(),
      locale: repository.getLocale(),
      autoPlayNarration: repository.getAutoPlay(),
    );
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    final repository = ref.read(settingsRepositoryProvider);
    await repository.setThemeMode(mode);
    state = state.copyWith(themeMode: mode);
  }

  Future<void> setLocale(String localeCode) async {
    final repository = ref.read(settingsRepositoryProvider);
    await repository.setLocale(localeCode);
    state = state.copyWith(locale: localeCode);
  }

  Future<void> toggleAutoPlay(bool value) async {
    final repository = ref.read(settingsRepositoryProvider);
    await repository.setAutoPlay(value);
    state = state.copyWith(autoPlayNarration: value);
  }
}

class SettingsState {
  final ThemeMode themeMode;
  final String? locale;
  final bool autoPlayNarration;

  SettingsState({
    required this.themeMode,
    this.locale,
    required this.autoPlayNarration,
  });

  SettingsState copyWith({
    ThemeMode? themeMode,
    String? locale,
    bool? autoPlayNarration,
  }) {
    return SettingsState(
      themeMode: themeMode ?? this.themeMode,
      locale: locale ?? this.locale,
      autoPlayNarration: autoPlayNarration ?? this.autoPlayNarration,
    );
  }
}
