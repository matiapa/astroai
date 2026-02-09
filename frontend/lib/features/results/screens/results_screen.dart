import 'dart:ui' as ui;
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:audioplayers/audioplayers.dart';

import 'package:astro_guide/core/theme/app_theme.dart';
import 'package:astro_guide/features/results/models/analysis_result.dart';
import 'package:astro_guide/features/results/providers/analysis_provider.dart';
import 'package:astro_guide/l10n/generated/app_localizations.dart';

/// Results Screen - The Revelation.
///
/// Displays actual analysis results from the provider.
class ResultsScreen extends ConsumerStatefulWidget {
  final String analysisId;

  const ResultsScreen({super.key, required this.analysisId});

  @override
  ConsumerState<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends ConsumerState<ResultsScreen> {
  ui.Image? _decodedImage;
  bool _hasInitialized = false;

  @override
  void initState() {
    super.initState();
    // Schedule check for after first frame to access ref properly
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkAndLoadAnalysis();
    });
  }

  void _checkAndLoadAnalysis() {
    if (_hasInitialized) return;
    _hasInitialized = true;

    final state = ref.read(analysisControllerProvider).value;

    // If current in-memory state matches, use it; otherwise load from storage
    if (state?.uid != widget.analysisId || state?.result == null) {
      ref
          .read(analysisControllerProvider.notifier)
          .loadFromUid(widget.analysisId);
    } else if (state?.imageBytes != null) {
      _decodeImage(state!.imageBytes!);
    }
  }

  Future<void> _decodeImage(List<int> bytes) async {
    try {
      final codec = await ui.instantiateImageCodec(Uint8List.fromList(bytes));
      final frame = await codec.getNextFrame();
      if (mounted) {
        setState(() {
          _decodedImage = frame.image;
        });
      }
    } catch (e) {
      debugPrint('Error decoding image for hotspots: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final analysisState = ref.watch(analysisControllerProvider);

    // Listen to decode image when loading from storage completes
    ref.listen(analysisControllerProvider, (previous, next) {
      next.whenData((state) {
        if (state.imageBytes != null && _decodedImage == null) {
          _decodeImage(state.imageBytes!);
        }
      });
    });

    final content = analysisState.when(
      data: (state) {
        if (state.result == null || state.imageBytes == null) {
          return _buildEmptyState(context);
        }
        return _buildContent(
          context,
          state.result!,
          state.imageBytes!,
          isAudioLoading: state.isAudioLoading,
        );
      },
      error: (err, stack) => Center(
        child: Text(
          'Error: $err',
          style: const TextStyle(color: AppColors.error),
        ),
      ),
      loading: () => const Center(
        child: CircularProgressIndicator(color: AppColors.cyanAccent),
      ),
    );

    return Scaffold(
      backgroundColor: AppColors.background,
      body: content,
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.broken_image, size: 64, color: AppColors.textMuted),
          const SizedBox(height: 16),
          Text(
            AppLocalizations.of(context)!.noAnalysisDataFound,
            style: AppTextStyles.headline(),
          ),
          const SizedBox(height: 8),
          FilledButton.tonal(
            onPressed: () => context.go('/observatory'),
            child: Text(AppLocalizations.of(context)!.returnToObservatory),
          ),
        ],
      ),
    );
  }

  Widget _buildContent(
    BuildContext context,
    AnalysisResult result,
    Uint8List imageBytes, {
    bool isAudioLoading = false,
  }) {
    final audioUrl = result.narration?.audioUrl;
    final hasAudio = audioUrl != null && audioUrl.isNotEmpty;

    return CustomScrollView(
      slivers: [
        // App Bar
        SliverAppBar(
          pinned: true,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: () => context.go('/observatory'),
          ),
          title: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: isAudioLoading
                      ? AppColors.cyanAccent
                      : AppColors.success,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                isAudioLoading
                    ? AppLocalizations.of(context)!.generatingAudioStatus
                    : AppLocalizations.of(context)!.analysisCompleteStatus,
                style: AppTextStyles.technical(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
          actions: [],
        ),

        // Content
        SliverToBoxAdapter(
          child: Column(
            children: [
              // Hero image with hotspots
              _HeroImageSection(
                imageBytes: imageBytes,
                decodedImage: _decodedImage,
                objects: result.identifiedObjects,
              ),

              const SizedBox(height: 24),

              // Narration Section
              if (result.narration != null) ...[
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Column(
                    children: [
                      Text(
                        result.narration!.title,
                        style: AppTextStyles.headline(),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 12),
                      _ExpandableNarrationText(text: result.narration!.text),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
              ],

              // Audio Section: Show player or loading indicator
              if (hasAudio) ...[
                _AudioPlayer(audioUrl: audioUrl),
                const SizedBox(height: 32),
              ] else if (isAudioLoading) ...[
                _AudioLoadingIndicator(),
                const SizedBox(height: 32),
              ],

              // Converse button
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () {
                      context.push('/chat/${widget.analysisId}');
                    },
                    icon: const Icon(Icons.auto_awesome),
                    label: Text(AppLocalizations.of(context)!.askAboutThisView),
                  ),
                ),
              ),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ],
    );
  }
}

class _HeroImageSection extends StatelessWidget {
  final Uint8List imageBytes;
  final ui.Image? decodedImage;
  final List<IdentifiedObject> objects;

  const _HeroImageSection({
    required this.imageBytes,
    required this.decodedImage,
    required this.objects,
  });

  @override
  Widget build(BuildContext context) {
    final mediaSize = MediaQuery.sizeOf(context);
    final screenHeight = mediaSize.height;
    final screenWidth = mediaSize.width;
    final isDesktop = screenWidth >= 600;

    // If we have image dimensions, we can constrain the aspect ratio
    // to match the image, ensuring hotspots align perfectly.
    final double aspectRatio = decodedImage != null
        ? decodedImage!.width / decodedImage!.height
        : 1.0;

    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: isDesktop ? screenWidth * 0.5 : screenWidth,
          maxHeight: screenHeight * 0.5,
        ),
        child: AspectRatio(
          aspectRatio: aspectRatio,
          child: InteractiveViewer(
            minScale: 1.0,
            maxScale: 4.0,
            child: Stack(
              fit: StackFit.expand,
              children: [
                // The Image
                Image.memory(imageBytes, fit: BoxFit.contain),
                // Hotspots
                if (decodedImage != null)
                  LayoutBuilder(
                    builder: (context, constraints) {
                      return Stack(
                        clipBehavior: Clip.none,
                        children: objects.map((obj) {
                          final double dx =
                              obj.pixelCoords.x / decodedImage!.width;
                          final double dy =
                              obj.pixelCoords.y / decodedImage!.height;

                          // Calculate pixel position in current container
                          final double x = dx * constraints.maxWidth;
                          final double y = dy * constraints.maxHeight;

                          return Positioned(
                            left: x - 24, // Centered (48/2)
                            top: y - 24,
                            child: _Hotspot(object: obj),
                          );
                        }).toList(),
                      );
                    },
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}


class _Hotspot extends StatefulWidget {
  final IdentifiedObject object;

  const _Hotspot({required this.object});

  @override
  State<_Hotspot> createState() => _HotspotState();
}

class _HotspotState extends State<_Hotspot>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _opacityAnimation;
  bool _isHovered = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);

    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 1.3,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));

    _opacityAnimation = Tween<double>(
      begin: 0.8,
      end: 0.4,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _showDetailDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => _ObjectDetailDialog(object: widget.object),
    );
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: Tooltip(
        message:
            '${widget.object.displayName}\n${AppLocalizations.of(context)!.tapForDetails}',
        preferBelow: false,
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: AppColors.cyanAccent.withValues(alpha: 0.3),
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.cyanAccent.withValues(alpha: 0.2),
              blurRadius: 8,
              spreadRadius: 1,
            ),
          ],
        ),
        textStyle: AppTextStyles.body(
          color: AppColors.textPrimary,
          fontSize: 12,
        ),
        child: GestureDetector(
          onTap: () => _showDetailDialog(context),
          behavior: HitTestBehavior.translucent,
          // Using LayoutBuilder+Positioned in parent means we don't need FractionalTranslation here
          // This 48x48 box is now perfectly centered on the coordinate
          child: SizedBox(
            width: 48,
            height: 48,
            child: Center(
              child: AnimatedBuilder(
                animation: _controller,
                builder: (context, child) {
                  return Stack(
                    alignment: Alignment.center,
                    children: [
                      // Outer pulsing ring
                      Transform.scale(
                        scale: _scaleAnimation.value,
                        child: Container(
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: AppColors.cyanAccent.withValues(
                                alpha: _opacityAnimation.value,
                              ),
                              width: 2,
                            ),
                          ),
                        ),
                      ),
                      // Inner dot with hover effect
                      AnimatedContainer(
                        duration: const Duration(milliseconds: 150),
                        width: _isHovered ? 14 : 10,
                        height: _isHovered ? 14 : 10,
                        decoration: BoxDecoration(
                          color: AppColors.cyanAccent,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.cyanAccent.withValues(
                                alpha: _isHovered ? 0.7 : 0.5,
                              ),
                              blurRadius: _isHovered ? 12 : 8,
                              spreadRadius: _isHovered ? 4 : 2,
                            ),
                          ],
                        ),
                      ),
                      // Tap indicator on hover
                      if (_isHovered)
                        Positioned(
                          bottom: -2,
                          child: Icon(
                            Icons.touch_app,
                            size: 12,
                            color: AppColors.cyanAccent.withValues(alpha: 0.8),
                          ),
                        ),
                    ],
                  );
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Dialog displaying detailed information about a celestial object.
class _ObjectDetailDialog extends StatelessWidget {
  final IdentifiedObject object;

  const _ObjectDetailDialog({required this.object});

  String _getTypeIcon() {
    switch (object.type.toLowerCase()) {
      case 'star':
        return '⭐';
      case 'galaxy':
        return '🌌';
      case 'nebula':
        return '🌫️';
      case 'cluster':
        return '✨';
      default:
        return '🔭';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        constraints: const BoxConstraints(maxWidth: 400),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: AppColors.cyanAccent.withValues(alpha: 0.3),
          ),
          boxShadow: [
            BoxShadow(
              color: AppColors.cyanAccent.withValues(alpha: 0.15),
              blurRadius: 24,
              spreadRadius: 4,
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Header
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    AppColors.cyanAccent.withValues(alpha: 0.1),
                    AppColors.surface,
                  ],
                ),
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(20),
                ),
              ),
              child: Row(
                children: [
                  Container(
                    width: 56,
                    height: 56,
                    decoration: BoxDecoration(
                      color: AppColors.cyanAccent.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: AppColors.cyanAccent.withValues(alpha: 0.3),
                      ),
                    ),
                    child: Center(
                      child: Text(
                        _getTypeIcon(),
                        style: const TextStyle(fontSize: 28),
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          object.displayName,
                          style: AppTextStyles.headline(fontSize: 18),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          object.subtype ?? object.type,
                          style: AppTextStyles.technical(
                            fontSize: 12,
                            color: AppColors.cyanAccent,
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close),
                    color: AppColors.textMuted,
                  ),
                ],
              ),
            ),

            // Content
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
              child: Column(
                children: [
                  // Coordinates
                  _DetailRow(
                    icon: Icons.explore,
                    label: AppLocalizations.of(context)!.coordinatesLabel,
                    value:
                        'RA: ${object.celestialCoords.raFormatted}\n'
                        'DEC: ${object.celestialCoords.decFormatted}',
                  ),

                  if (object.distanceLightyears != null) ...[
                    const SizedBox(height: 12),
                    _DetailRow(
                      icon: Icons.straighten,
                      label: AppLocalizations.of(context)!.distanceLabel,
                      value: object.distanceFormatted,
                    ),
                  ],

                  if (object.magnitudeVisual != null) ...[
                    const SizedBox(height: 12),
                    _DetailRow(
                      icon: Icons.brightness_6,
                      label: AppLocalizations.of(context)!.magnitudeLabel,
                      value: object.magnitudeVisual!.toStringAsFixed(2),
                    ),
                  ],

                  if (object.spectralType != null &&
                      object.spectralType!.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    _DetailRow(
                      icon: Icons.science,
                      label: AppLocalizations.of(context)!.spectralTypeLabel,
                      value: object.spectralType!,
                    ),
                  ],

                  if (object.morphologicalType != null &&
                      object.morphologicalType!.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    _DetailRow(
                      icon: Icons.category,
                      label: AppLocalizations.of(context)!.morphologyLabel,
                      value: object.morphologicalType!,
                    ),
                  ],

                  if (object.alternativeNames != null &&
                      object.alternativeNames!.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    _DetailRow(
                      icon: Icons.label,
                      label: AppLocalizations.of(context)!.alsoKnownAsLabel,
                      value: object.alternativeNames!.join(', '),
                    ),
                  ],

                  if (object.legend != null && object.legend!.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceElevated,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        object.legend!,
                        style: AppTextStyles.body(
                          color: AppColors.textSecondary,
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// A row displaying an icon, label, and value for the detail dialog.
class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: AppColors.cyanAccent.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, size: 16, color: AppColors.cyanAccent),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: AppTextStyles.technical(
                  fontSize: 10,
                  color: AppColors.textMuted,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: AppTextStyles.body(
                  color: AppColors.textPrimary,
                  fontSize: 13,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Widget shown while audio is being generated.
class _AudioLoadingIndicator extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface.withOpacity(0.5),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.cyanAccent.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: AppColors.cyanAccent,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                AppLocalizations.of(context)!.generatingAudioTitle,
                style: AppTextStyles.technical(
                  fontSize: 11,
                  color: AppColors.cyanAccent,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Placeholder waveform bars (inactive state)
          SizedBox(
            height: 32,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                20,
                (index) => Container(
                  width: 3,
                  height: 8 + (index % 4) * 4.0,
                  margin: const EdgeInsets.symmetric(horizontal: 1.5),
                  decoration: BoxDecoration(
                    color: AppColors.textMuted.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            AppLocalizations.of(context)!.audioNarrationPending,
            style: AppTextStyles.body(fontSize: 12, color: AppColors.textMuted),
          ),
        ],
      ),
    );
  }
}

class _AudioPlayer extends StatefulWidget {
  final String audioUrl;
  const _AudioPlayer({required this.audioUrl});

  @override
  State<_AudioPlayer> createState() => _AudioPlayerState();
}

class _AudioPlayerState extends State<_AudioPlayer> {
  late AudioPlayer _player;
  bool _isPlaying = false;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();
    _initAudio();
  }

  Future<void> _initAudio() async {
    try {
      // Listen to player state changes
      _player.onPlayerStateChanged.listen((state) {
        if (mounted) {
          setState(() => _isPlaying = state == PlayerState.playing);
        }
      });

      // Listen to position changes
      _player.onPositionChanged.listen((pos) {
        if (mounted) {
          setState(() => _position = pos);
        }
      });

      // Listen to duration changes
      _player.onDurationChanged.listen((dur) {
        if (mounted) {
          setState(() => _duration = dur);
        }
      });

      // Load the audio source
      await _player.setSourceUrl(widget.audioUrl);
      if (mounted) {
        setState(() => _isLoading = false);
      }
    } catch (e, stackTrace) {
      debugPrint('Audio player error: $e');
      debugPrint('Stack trace: $stackTrace');
      debugPrint('Audio URL was: ${widget.audioUrl}');
      if (mounted) {
        setState(() {
          _isLoading = false;
          _error = AppLocalizations.of(context)!.audioLoadError(e);
        });
      }
    }
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  Future<void> _togglePlay() async {
    if (_isPlaying) {
      await _player.pause();
    } else {
      await _player.resume();
    }
  }

  Future<void> _seekBackward() async {
    final newPosition = _position - const Duration(seconds: 10);
    await _player.seek(
      newPosition < Duration.zero ? Duration.zero : newPosition,
    );
  }

  Future<void> _seekForward() async {
    final newPosition = _position + const Duration(seconds: 10);
    await _player.seek(newPosition > _duration ? _duration : newPosition);
  }

  String _formatDuration(Duration d) {
    final minutes = d.inMinutes;
    final seconds = d.inSeconds % 60;
    return '$minutes:${seconds.toString().padLeft(2, '0')}';
  }

  double get _progress {
    if (_duration.inMilliseconds == 0) return 0.0;
    return _position.inMilliseconds / _duration.inMilliseconds;
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: Text(
          _error!,
          style: AppTextStyles.body(color: AppColors.error),
          textAlign: TextAlign.center,
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        children: [
          Container(
            height: 40,
            margin: const EdgeInsets.only(bottom: 16),
            child: CustomPaint(
              size: const Size(double.infinity, 40),
              painter: _WaveformPainter(progress: _progress),
            ),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                _formatDuration(_position),
                style: AppTextStyles.technical(
                  fontSize: 12,
                  color: AppColors.textMuted,
                ),
              ),
              const SizedBox(width: 16),
              IconButton(
                icon: const Icon(Icons.replay_10),
                color: AppColors.textSecondary,
                onPressed: _seekBackward,
              ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: _isLoading ? null : _togglePlay,
                child: Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    gradient: AppColors.cyanGradient,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.cyanAccent.withValues(alpha: 0.3),
                        blurRadius: 16,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: _isLoading
                      ? const Center(
                          child: SizedBox(
                            width: 24,
                            height: 24,
                            child: CircularProgressIndicator(
                              color: AppColors.background,
                              strokeWidth: 2,
                            ),
                          ),
                        )
                      : Icon(
                          _isPlaying ? Icons.pause : Icons.play_arrow,
                          color: AppColors.background,
                          size: 32,
                        ),
                ),
              ),
              const SizedBox(width: 8),
              IconButton(
                icon: const Icon(Icons.forward_10),
                color: AppColors.textSecondary,
                onPressed: _seekForward,
              ),
              const SizedBox(width: 16),
              Text(
                _formatDuration(_duration),
                style: AppTextStyles.technical(
                  fontSize: 12,
                  color: AppColors.textMuted,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _WaveformPainter extends CustomPainter {
  final double progress;

  _WaveformPainter({required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppColors.cyanAccent.withValues(alpha: 0.3)
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    final activePaint = Paint()
      ..color = AppColors.cyanAccent
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    final centerY = size.height / 2;
    // Draw pseudo-waveform
    for (var i = 0; i < size.width; i += 4) {
      // Create a fake wave pattern based on index
      final height = 10 + (i % 20).toDouble();
      final p = i / size.width;

      final start = Offset(i.toDouble(), centerY - height / 2);
      final end = Offset(i.toDouble(), centerY + height / 2);

      canvas.drawLine(start, end, p <= progress ? activePaint : paint);
    }
  }

  @override
  bool shouldRepaint(covariant _WaveformPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}

class _ExpandableNarrationText extends StatefulWidget {
  final String text;
  static const int trimLength = 300;

  const _ExpandableNarrationText({required this.text});

  @override
  State<_ExpandableNarrationText> createState() =>
      _ExpandableNarrationTextState();
}

class _ExpandableNarrationTextState extends State<_ExpandableNarrationText> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final bool canExpand =
        widget.text.length > _ExpandableNarrationText.trimLength;
    final String displayText = _isExpanded || !canExpand
        ? widget.text
        : '${widget.text.substring(0, _ExpandableNarrationText.trimLength)}...';

    return Column(
      children: [
        AnimatedSize(
          duration: const Duration(milliseconds: 300),
          alignment: Alignment.topCenter,
          curve: Curves.easeInOut,
          child: Text(
            displayText,
            style: AppTextStyles.body(
              color: AppColors.textSecondary,
            ).copyWith(height: 1.5),
            textAlign: TextAlign.justify,
          ),
        ),
        if (canExpand) ...[
          const SizedBox(height: 8),
          TextButton(
            onPressed: () {
              setState(() {
                _isExpanded = !_isExpanded;
              });
            },
            style: TextButton.styleFrom(foregroundColor: AppColors.cyanAccent),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _isExpanded
                      ? AppLocalizations.of(context)!.viewLess
                      : AppLocalizations.of(context)!.viewMore,
                ),
                const SizedBox(width: 4),
                Icon(
                  _isExpanded ? Icons.expand_less : Icons.expand_more,
                  size: 16,
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}
