import 'package:flutter/material.dart';
import 'package:flutter_ai_toolkit/flutter_ai_toolkit.dart';
import 'package:a2a/a2a.dart';
import 'package:go_router/go_router.dart';

import 'package:astro_guide/core/config/app_config.dart';
import 'package:astro_guide/core/theme/app_theme.dart';
import 'package:astro_guide/features/chat/providers/a2a_provider.dart';
import 'package:astro_guide/features/chat/theme/chat_theme.dart';
import 'package:astro_guide/features/logbook/providers/logbook_provider.dart';
import 'package:astro_guide/features/results/models/analysis_result.dart';
import 'package:astro_guide/l10n/generated/app_localizations.dart';

/// Results Chat Screen -- contextual chat about a specific analysis.
///
/// Accessed from the results screen "Ask with AI" button. Loads the analysis
/// data for the given [analysisId] and creates an [A2aProvider] with context
/// about the identified objects, narration, and coordinates so the Atlas
/// agent can provide informed, relevant responses.
class ResultsChatScreen extends StatefulWidget {
  /// The ID of the analysis to provide as context.
  final String analysisId;

  const ResultsChatScreen({super.key, required this.analysisId});

  @override
  State<ResultsChatScreen> createState() => _ResultsChatScreenState();
}

class _ResultsChatScreenState extends State<ResultsChatScreen> {
  A2aProvider? _provider;
  String? _analysisTitle;
  String? _error;

  @override
  void initState() {
    super.initState();
    _initProvider();
  }

  void _initProvider() {
    try {
      final entry = logbookServiceInstance.getEntry(widget.analysisId);
      if (entry == null) {
        setState(() => _error = 'Analysis not found');
        return;
      }

      final result = entry.analysisResult;
      final context = _buildContextString(result);
      final client = A2AClient(AppConfig.a2aAgentUrl);

      setState(() {
        _analysisTitle = result.narration?.title;
        _provider = A2aProvider(
          client: client,
          initialContext: context,
        );
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  /// Builds a context string from the analysis result to inject into the
  /// first A2A message, giving Atlas awareness of what the user is viewing.
  String _buildContextString(AnalysisResult result) {
    final buffer = StringBuffer();

    buffer.writeln('[Context: The user is viewing a sky analysis with the following data.]');

    if (result.narration != null) {
      buffer.writeln('Title: ${result.narration!.title}');
      buffer.writeln('Narration: ${result.narration!.text}');
    }

    if (result.plateSolving != null) {
      final ps = result.plateSolving!;
      buffer.writeln(
        'Center coordinates: RA ${ps.centerRaDeg.toStringAsFixed(4)}deg, '
        'Dec ${ps.centerDecDeg.toStringAsFixed(4)}deg',
      );
    }

    if (result.identifiedObjects.isNotEmpty) {
      buffer.writeln('Identified objects:');
      for (final obj in result.identifiedObjects) {
        final parts = <String>[
          obj.displayName,
          'type: ${obj.type}',
        ];
        if (obj.distanceLightyears != null) {
          parts.add('distance: ${obj.distanceFormatted}');
        }
        if (obj.magnitudeVisual != null) {
          parts.add('magnitude: ${obj.magnitudeVisual!.toStringAsFixed(2)}');
        }
        if (obj.spectralType != null && obj.spectralType!.isNotEmpty) {
          parts.add('spectral: ${obj.spectralType}');
        }
        if (obj.legend != null && obj.legend!.isNotEmpty) {
          parts.add('legend: ${obj.legend}');
        }
        buffer.writeln('  - ${parts.join(", ")}');
      }
    }

    buffer.writeln('[End of context. The user\'s question follows.]');

    return buffer.toString();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
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
            Flexible(
              child: Text(
                _analysisTitle ?? l10n.chatAtlasTitle,
                style: AppTextStyles.headline(fontSize: 16),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
        centerTitle: true,
      ),
      body: _buildBody(l10n),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48, color: AppColors.error),
            const SizedBox(height: 16),
            Text(
              _error!,
              style: AppTextStyles.body(color: AppColors.textSecondary),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => context.pop(),
              child: Text(l10n.goBack),
            ),
          ],
        ),
      );
    }

    if (_provider == null) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.cyanAccent),
      );
    }

    return LlmChatView(
      provider: _provider!,
      style: ChatTheme.deepSpaceStyle,
      welcomeMessage: l10n.chatResultsWelcome,
    );
  }
}
