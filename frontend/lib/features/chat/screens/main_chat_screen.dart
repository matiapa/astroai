import 'package:flutter/material.dart';
import 'package:flutter_ai_toolkit/flutter_ai_toolkit.dart';
import 'package:a2a/a2a.dart';

import 'package:astro_guide/core/config/app_config.dart';
import 'package:astro_guide/core/theme/app_theme.dart';
import 'package:astro_guide/features/chat/providers/a2a_provider.dart';
import 'package:astro_guide/features/chat/theme/chat_theme.dart';
import 'package:astro_guide/l10n/generated/app_localizations.dart';

/// Main Chat Screen -- accessible as the 4th tab in the navigation bar.
///
/// Provides a general-purpose conversational interface with the Atlas AI
/// agent. Users can ask about astronomy, constellations, celestial events,
/// or anything related to the night sky.
class MainChatScreen extends StatefulWidget {
  const MainChatScreen({super.key});

  @override
  State<MainChatScreen> createState() => _MainChatScreenState();
}

class _MainChatScreenState extends State<MainChatScreen> {
  late final A2aProvider _provider;

  @override
  void initState() {
    super.initState();
    final client = A2AClient(
      AppConfig.a2aAgentUrl,
      agentCardBackgroundFetch: false,
    );
    _provider = A2aProvider(client: client);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.cyanAccent.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.auto_awesome,
                color: AppColors.cyanAccent,
                size: 18,
              ),
            ),
            const SizedBox(width: 10),
            Text(
              l10n.chatAtlasTitle,
              style: AppTextStyles.headline(fontSize: 18),
            ),
          ],
        ),
        centerTitle: true,
      ),
      body: LlmChatView(
        provider: _provider,
        style: ChatTheme.deepSpaceStyle,
        welcomeMessage: l10n.chatWelcomeMessage,
        suggestions: [
          l10n.chatSuggestion1,
          l10n.chatSuggestion2,
          l10n.chatSuggestion3,
        ],
      ),
    );
  }
}
