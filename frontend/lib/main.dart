import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:astro_guide/l10n/generated/app_localizations.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hive_ce_flutter/hive_flutter.dart';

import 'core/navigation/app_router.dart';
import 'features/settings/data/settings_repository.dart';
import 'features/settings/providers/settings_provider.dart';
import 'core/theme/app_theme.dart';
import 'features/chat/providers/chat_session_provider.dart';
import 'features/logbook/providers/logbook_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Hive for local storage
  await Hive.initFlutter();

  // Initialize logbook service (registers adapter and opens box)
  await logbookServiceInstance.initialize();

  // Initialize chat session service (registers adapter and opens box)
  await chatSessionServiceInstance.initialize();

  // Set preferred orientations
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Set system UI overlay style for dark theme
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      systemNavigationBarColor: AppColors.background,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  runApp(
    ProviderScope(
      overrides: [
        settingsRepositoryProvider.overrideWithValue(
          SettingsRepository(await SharedPreferences.getInstance()),
        ),
      ],
      child: const AstroGuideApp(),
    ),
  );
}

/// AstroGuide - AI-powered astronomy assistant
///
/// Main application widget that configures theme and routing.
class AstroGuideApp extends ConsumerWidget {
  const AstroGuideApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    
    return MaterialApp.router(
      onGenerateTitle: (context) => AppLocalizations.of(context)!.appTitle,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      themeMode: settings.themeMode,
      locale: settings.locale != null ? Locale(settings.locale!) : null,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      routerConfig: appRouter,
    );
  }
}
