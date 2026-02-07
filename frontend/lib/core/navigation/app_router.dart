import 'package:go_router/go_router.dart';

import 'package:astro_guide/features/observatory/screens/observatory_screen.dart';
import 'package:astro_guide/features/logbook/screens/logbook_screen.dart';
import 'package:astro_guide/features/settings/screens/settings_screen.dart';
import 'package:astro_guide/features/results/screens/results_screen.dart';
import 'package:astro_guide/features/chat/screens/main_chat_screen.dart';
import 'package:astro_guide/features/chat/screens/results_chat_screen.dart';
import 'responsive_scaffold.dart';

/// Application routes configuration using GoRouter.
///
/// Main navigation structure:
/// - /observatory (home) - Camera/capture screen
/// - /logbook - History gallery
/// - /chat - General chat with Atlas AI agent
/// - /settings - App preferences
/// - /results/:id - Analysis results (accessed from observatory or logbook)
/// - /chat/:id - Contextual chat about a specific analysis
final GoRouter appRouter = GoRouter(
  initialLocation: '/observatory',
  routes: [
    // Shell route for bottom navigation
    ShellRoute(
      builder: (context, state, child) {
        return ResponsiveScaffold(currentPath: state.uri.path, child: child);
      },
      routes: [
        GoRoute(
          path: '/observatory',
          name: 'observatory',
          pageBuilder: (context, state) =>
              const NoTransitionPage(child: ObservatoryScreen()),
        ),
        GoRoute(
          path: '/logbook',
          name: 'logbook',
          pageBuilder: (context, state) =>
              const NoTransitionPage(child: LogbookScreen()),
        ),
        GoRoute(
          path: '/chat',
          name: 'chat',
          pageBuilder: (context, state) =>
              const NoTransitionPage(child: MainChatScreen()),
        ),
        GoRoute(
          path: '/settings',
          name: 'settings',
          pageBuilder: (context, state) =>
              const NoTransitionPage(child: SettingsScreen()),
        ),
      ],
    ),
    // Results screen (outside shell route - no bottom nav)
    GoRoute(
      path: '/results/:id',
      name: 'results',
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        return ResultsScreen(analysisId: id);
      },
    ),
    // Results chat screen (outside shell route - no bottom nav)
    GoRoute(
      path: '/chat/:id',
      name: 'results_chat',
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        return ResultsChatScreen(analysisId: id);
      },
    ),
  ],
);
