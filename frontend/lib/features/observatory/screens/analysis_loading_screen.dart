import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:astro_guide/core/theme/app_theme.dart';
import 'package:astro_guide/features/results/providers/analysis_provider.dart';
import 'package:astro_guide/features/results/models/analysis_result.dart'; // Added import
import 'package:astro_guide/l10n/generated/app_localizations.dart';

class AnalysisLoadingScreen extends ConsumerStatefulWidget {
  const AnalysisLoadingScreen({super.key});

  @override
  ConsumerState<AnalysisLoadingScreen> createState() =>
      _AnalysisLoadingScreenState();
}

class _AnalysisLoadingScreenState extends ConsumerState<AnalysisLoadingScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 4),
      vsync: this,
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Check if analysis is already done when first building
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final currentState = ref.read(analysisControllerProvider).valueOrNull;
      if (currentState?.result?.narration != null &&
          currentState?.uid != null) {
        context.pushReplacement('/results/${currentState!.uid}');
      }
    });

    // Listen for narration completion to navigate away (don't wait for audio)
    ref.listen(analysisControllerProvider, (previous, next) {
      if (!mounted) return;
      next.when(
        data: (state) {
          // Navigate when narration is available (not waiting for audio)
          if (state.result?.narration != null && state.uid != null) {
            // Replace this screen with the results screen using UID
            context.pushReplacement('/results/${state.uid}');
          }
        },
        error: (error, stack) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                AppLocalizations.of(context)!.analysisFailed(error),
              ),
              backgroundColor: AppColors.error,
            ),
          );
          if (context.canPop()) {
            context.pop(); // Go back to observatory
          }
        },
        loading: () {}, // Stay here
      );
    });

    final state = ref.watch(analysisControllerProvider);
    final currentStep =
        state.valueOrNull?.loadingStep ?? AnalysisStep.analyzingImage;
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Background Effect (Subtle pulsing or gradient)
          Container(
            decoration: BoxDecoration(
              gradient: RadialGradient(
                center: Alignment.center,
                radius: 1.5,
                colors: [AppColors.background, Colors.black],
              ),
            ),
          ),

          SafeArea(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Fancy Animation Placeholder (Orbiting planets)
                SizedBox(
                  height: 200,
                  width: 200,
                  child: CustomPaint(painter: _OrbitPainter(_controller)),
                ),
                const SizedBox(height: 48),

                // Progress Text
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 500),
                  child: Text(
                    _getStepText(currentStep, l10n),
                    key: ValueKey(currentStep),
                    style: AppTextStyles.headline(
                      fontSize: 24,
                    ).copyWith(color: AppColors.cyanAccent, letterSpacing: 1.2),
                    textAlign: TextAlign.center,
                  ),
                ),
                const SizedBox(height: 16),

                // Sub-text or explanation
                Text(
                  _getStepDescription(currentStep, l10n),
                  style: AppTextStyles.body(color: AppColors.textMuted),
                  textAlign: TextAlign.center,
                ),

                const SizedBox(height: 64),
                // Linear Progress Indicator
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 48),
                  child: LinearProgressIndicator(
                    backgroundColor: AppColors.surfaceElevated,
                    color: AppColors.cyanAccent,
                    minHeight: 4,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _getStepText(AnalysisStep step, AppLocalizations l10n) {
    switch (step) {
      case AnalysisStep.analyzingImage:
        return l10n.analyzingCosmos;
      case AnalysisStep.generatingNarration:
        return l10n.consultingArchives;
      case AnalysisStep.generatingAudio:
        return l10n.synthesizingVoice;
      case AnalysisStep.finished:
        return l10n.discoveryComplete;
      default:
        return l10n.processing;
    }
  }

  String _getStepDescription(AnalysisStep step, AppLocalizations l10n) {
    switch (step) {
      case AnalysisStep.analyzingImage:
        return l10n.identifyingCelestialObjects;
      case AnalysisStep.generatingNarration:
        return l10n.craftingStory;
      case AnalysisStep.generatingAudio:
        return l10n.preparingAudioGuide;
      case AnalysisStep.finished:
        return l10n.preparingResults;
      default:
        return l10n.pleaseWait;
    }
  }
}

class _OrbitPainter extends CustomPainter {
  final Animation<double> animation;

  _OrbitPainter(this.animation) : super(repaint: animation);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5
      ..color = AppColors.cyanAccent.withValues(alpha: 0.3);

    // Draw orbits
    canvas.drawCircle(center, 40, paint);
    canvas.drawCircle(
      center,
      70,
      paint..color = AppColors.violetAccent.withValues(alpha: 0.2),
    );

    // Draw moving planet 1
    final planetPaint = Paint()
      ..style = PaintingStyle.fill
      ..color = AppColors.cyanAccent;

    final angle1 = animation.value * 2 * math.pi;
    final planet1X = center.dx + 40 * math.cos(angle1);
    final planet1Y = center.dy + 40 * math.sin(angle1);
    canvas.drawCircle(Offset(planet1X, planet1Y), 4, planetPaint);

    // Draw moving planet 2 (slower, further out)
    final planet2Paint = Paint()
      ..style = PaintingStyle.fill
      ..color = AppColors.violetAccent;

    final angle2 = animation.value * 2 * math.pi * 0.7 + 1.0; // Offset start
    final planet2X = center.dx + 70 * math.cos(angle2);
    final planet2Y = center.dy + 70 * math.sin(angle2);
    canvas.drawCircle(Offset(planet2X, planet2Y), 6, planet2Paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
