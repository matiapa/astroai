import 'package:go_router/go_router.dart';

import 'package:astro_guide/features/observatory/screens/observatory_screen.dart';
import 'package:astro_guide/features/logbook/screens/logbook_screen.dart';
import 'package:astro_guide/features/settings/screens/settings_screen.dart';
import 'package:astro_guide/features/results/screens/results_screen.dart';
import 'package:astro_guide/features/observatory/screens/analysis_loading_screen.dart';
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
        GoRoute(
          path: '/results/:id',
          name: 'results',
          pageBuilder: (context, state) {
            final id = state.pathParameters['id']!;
            return NoTransitionPage(child: ResultsScreen(analysisId: id));
          },
        ),
        GoRoute(
          path: '/analyze/loading',
          name: 'analysis_loading',
          pageBuilder: (context, state) =>
              const NoTransitionPage(child: AnalysisLoadingScreen()),
        ),
        GoRoute(
          path: '/chat/:id',
          name: 'results_chat',
          pageBuilder: (context, state) {
            final id = state.pathParameters['id']!;
            return NoTransitionPage(child: ResultsChatScreen(analysisId: id));
          },
        ),
      ],
    ),
  ],
);
