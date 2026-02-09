import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import 'package:astro_guide/core/theme/app_theme.dart';
import 'package:astro_guide/features/results/providers/analysis_provider.dart';
import 'package:astro_guide/features/observatory/screens/analysis_loading_screen.dart';
import 'package:astro_guide/l10n/generated/app_localizations.dart';

/// Observatory Screen - The main camera/capture screen.
///
/// Features:
/// - Image capture via camera or gallery
/// - Reference catalog for sample images
/// - Manual control sliders (Zoom supported on Web; ISO/Exposure only on Mobile)
class ObservatoryScreen extends ConsumerStatefulWidget {
  const ObservatoryScreen({super.key});

  @override
  ConsumerState<ObservatoryScreen> createState() => _ObservatoryScreenState();
}

class _ObservatoryScreenState extends ConsumerState<ObservatoryScreen> {

  final ImagePicker _picker = ImagePicker();
  Uint8List? _selectedImageBytes;
  String? _selectedImageName;
  bool _isLoading = false;

  CameraController? _cameraController;
  bool _isCameraInitialized = false;

  // Camera Control State
  double _minZoom = 1.0;
  double _maxZoom = 1.0;
  double _currentZoom = 1.0;

  double _minExposure = 0.0;
  double _maxExposure = 0.0;
  double _currentExposure = 0.0;

  // ISO is simulated on some Android devices by exposure compensation,
  // currently we will track it but standard CameraX/Camera2 doesn't always expose raw ISO easily
  // via this plugin. We will use exposure offset which is standard.
  // For the purpose of this task, we will stick to Exposure Offset and Zoom.

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) return;

      // Use the first back camera
      final camera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );

      _cameraController = CameraController(
        camera,
        ResolutionPreset.high,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.jpeg,
      );

      await _cameraController!.initialize();
      if (!mounted) return;

      // Set initial zoom levels
      try {
        _minZoom = await _cameraController!.getMinZoomLevel();
        _maxZoom = await _cameraController!.getMaxZoomLevel();
      } catch (e) {
        debugPrint('Zoom level not supported: $e');
        _minZoom = 1.0;
        _maxZoom = 1.0;
      }

      // Set initial exposure levels (Mobile Only)
      if (!kIsWeb) {
        try {
          _minExposure = await _cameraController!.getMinExposureOffset();
          _maxExposure = await _cameraController!.getMaxExposureOffset();
        } catch (e) {
          debugPrint('Exposure offset not supported: $e');
        }
      }

      setState(() {
        _isCameraInitialized = true;
      });
    } catch (e) {
      debugPrint('Camera initialization error: $e');
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  /// Loads an image from assets for the catalog.
  Future<void> _loadCatalogAsset(String assetPath, String name) async {
    try {
      final bytes = await rootBundle.load('assets/catalog/$assetPath.gif');
      setState(() {
        _selectedImageBytes = bytes.buffer.asUint8List();
        _selectedImageName = name;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              AppLocalizations.of(context)!.assetNotFound(assetPath),
            ),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Future<void> _pickFromGallery() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 2048,
        maxHeight: 2048,
      );
      if (image != null) {
        final bytes = await image.readAsBytes();
        setState(() {
          _selectedImageBytes = bytes;
          _selectedImageName = image.name;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(AppLocalizations.of(context)!.errorPickingImage(e)),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Future<void> _captureFromCamera() async {
    // If we have a native camera controller, use it
    if (_cameraController != null && _cameraController!.value.isInitialized) {
      try {
        setState(() => _isLoading = true);
        final XFile image = await _cameraController!.takePicture();
        final bytes = await image.readAsBytes();
        setState(() {
          _selectedImageBytes = bytes;
          _selectedImageName =
              'capture_${DateTime.now().millisecondsSinceEpoch}.jpg';
        });
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(AppLocalizations.of(context)!.captureError(e)),
              backgroundColor: AppColors.error,
            ),
          );
        }
      } finally {
        if (mounted) setState(() => _isLoading = false);
      }
    } else {
      // Fallback to ImagePicker camera (e.g. if controller init failed)
      try {
        setState(() => _isLoading = true);
        final XFile? image = await _picker.pickImage(
          source: ImageSource.camera,
          maxWidth: 2048,
          maxHeight: 2048,
        );
        if (image != null) {
          final bytes = await image.readAsBytes();
          setState(() {
            _selectedImageBytes = bytes;
            _selectedImageName = image.name;
          });
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                AppLocalizations.of(context)!.cameraNotAvailable(e),
              ),
              backgroundColor: AppColors.error,
            ),
          );
        }
      } finally {
        if (mounted) setState(() => _isLoading = false);
      }
    }
  }

  void _showCatalog() {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (context) => _CatalogBottomSheet(
        onSelect: (asset, name) {
          _loadCatalogAsset(asset, name);
          Navigator.pop(context);
        },
      ),
    );
  }

  Future<void> _analyzeImage() async {
    if (_selectedImageBytes == null) return;

    // Trigger analysis via provider
    ref
        .read(analysisControllerProvider.notifier)
        .analyze(
          AnalysisInput.bytes(
            _selectedImageBytes!,
            _selectedImageName ?? 'capture.jpg',
          ),
        );

    // Navigate to loading screen immediately
    Navigator.of(context).push(
      MaterialPageRoute(builder: (context) => const AnalysisLoadingScreen()),
    );
  }

  void _clearImage() {
    setState(() {
      _selectedImageBytes = null;
      _selectedImageName = null;
    });
    ref.read(analysisControllerProvider.notifier).reset();
  }

  // Camera Control Methods
  Future<void> _setZoom(double zoom) async {
    if (_cameraController == null) return;
    try {
      await _cameraController!.setZoomLevel(zoom);
      setState(() => _currentZoom = zoom);
    } catch (e) {
      debugPrint('Error setting zoom: $e');
    }
  }

  Future<void> _setExposureOffset(double offset) async {
    if (_cameraController == null) return;
    try {
      await _cameraController!.setExposureOffset(offset);
      setState(() => _currentExposure = offset);
    } catch (e) {
      debugPrint('Error setting exposure: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    final analysisState = ref.watch(analysisControllerProvider);
    final isAnalyzing = analysisState.isLoading;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Image preview or capture prompt
          if (_selectedImageBytes != null)
            _ImagePreview(
              imageBytes: _selectedImageBytes!,
              imageName: _selectedImageName,
              onClear: _clearImage,
            )
          else if (_isCameraInitialized && _cameraController != null)
            Center(
              child: CameraPreview(
                _cameraController!,
                child: const _ViewfinderOverlay(),
              ),
            )
          // Fallback UI if camera not ready
          else
            _CapturePrompt(
              isLoading: _isLoading,
              onCapture: _captureFromCamera,
            ),

          // Controls panel at bottom
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: _ControlsPanel(
              hasImage: _selectedImageBytes != null,
              isAnalyzing: isAnalyzing,
              onGalleryPressed: _pickFromGallery,
              onCapturePressed: _selectedImageBytes != null
                  ? _analyzeImage
                  : _captureFromCamera,
              onCatalogPressed: _showCatalog,
              // Pass Camera Controls
              showCameraControls: _selectedImageBytes == null &&
                  _isCameraInitialized,
              currentZoom: _currentZoom,
              minZoom: _minZoom,
              maxZoom: _maxZoom,
              onZoomChanged: _setZoom,
              currentExposure: _currentExposure,
              minExposure: _minExposure,
              maxExposure: _maxExposure,
              onExposureChanged: _setExposureOffset,
            ),
          ),
        ],
      ),
    );
  }
}

class _CapturePrompt extends StatelessWidget {
  final bool isLoading;
  final VoidCallback onCapture;

  const _CapturePrompt({required this.isLoading, required this.onCapture});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onCapture,
      child: Container(
        color: AppColors.background,
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (isLoading)
                const CircularProgressIndicator(color: AppColors.cyanAccent)
              else
                const Icon(
                  Icons.camera_alt,
                  size: 64,
                  color: AppColors.cyanMuted,
                ),
              const SizedBox(height: 16),
              Text(
                isLoading
                    ? AppLocalizations.of(context)!.openingCamera
                    : AppLocalizations.of(context)!.loadingCamera,
                style: const TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 16,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ImagePreview extends StatelessWidget {
  final Uint8List imageBytes;
  final String? imageName;
  final VoidCallback onClear;

  const _ImagePreview({
    required this.imageBytes,
    this.imageName,
    required this.onClear,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        InteractiveViewer(
          minScale: 0.5,
          maxScale: 4.0,
          child: Image.memory(imageBytes, fit: BoxFit.contain),
        ),
        // Clear button
        Positioned(
          top: MediaQuery.of(context).padding.top + 8,
          right: 16,
          child: IconButton(
            onPressed: onClear,
            icon: const Icon(Icons.close),
            style: IconButton.styleFrom(
              backgroundColor: AppColors.surface.withValues(alpha: 0.8),
              foregroundColor: AppColors.textPrimary,
            ),
          ),
        ),
        // Image name badge
        if (imageName != null)
          Positioned(
            top: MediaQuery.of(context).padding.top + 8,
            left: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: AppColors.surface.withValues(alpha: 0.8),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                imageName!,
                style: AppTextStyles.technical(fontSize: 12),
              ),
            ),
          ),
      ],
    );
  }
}

class _ViewfinderOverlay extends StatelessWidget {
  const _ViewfinderOverlay();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return Center(
          child: CustomPaint(
            size: Size(constraints.maxWidth, constraints.maxHeight),
            painter: _ViewfinderPainter(),
          ),
        );
      },
    );
  }
}

class _ViewfinderPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppColors.cyanAccent.withValues(alpha: 0.6)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;

    final center = Offset(size.width / 2, size.height / 2);
    // Use smaller dimension for radius to ensure it fits on screen
    final radius = (size.width < size.height ? size.width : size.height) * 0.4;

    // Outer circle
    canvas.drawCircle(center, radius, paint);

    // Inner circle
    canvas.drawCircle(center, radius * 0.6, paint);

    // Crosshair lines
    const crossLength = 15.0;
    // Top
    canvas.drawLine(
      Offset(center.dx, center.dy - radius + 10),
      Offset(center.dx, center.dy - radius + 10 + crossLength),
      paint,
    );
    // Bottom
    canvas.drawLine(
      Offset(center.dx, center.dy + radius - 10 - crossLength),
      Offset(center.dx, center.dy + radius - 10),
      paint,
    );
    // Left
    canvas.drawLine(
      Offset(center.dx - radius + 10, center.dy),
      Offset(center.dx - radius + 10 + crossLength, center.dy),
      paint,
    );
    // Right
    canvas.drawLine(
      Offset(center.dx + radius - 10 - crossLength, center.dy),
      Offset(center.dx + radius - 10, center.dy),
      paint,
    );

    // Center dot
    final dotPaint = Paint()
      ..color = AppColors.cyanAccent
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, 3, dotPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _ControlsPanel extends StatelessWidget {
  final bool hasImage;
  final bool isAnalyzing;
  final VoidCallback onGalleryPressed;
  final VoidCallback onCapturePressed;
  final VoidCallback onCatalogPressed;

  // Camera Control Props
  final bool showCameraControls;
  final double currentZoom;
  final double minZoom;
  final double maxZoom;
  final ValueChanged<double> onZoomChanged;

  final double currentExposure;
  final double minExposure;
  final double maxExposure;
  final ValueChanged<double> onExposureChanged;

  const _ControlsPanel({
    required this.hasImage,
    required this.isAnalyzing,
    required this.onGalleryPressed,
    required this.onCapturePressed,
    required this.onCatalogPressed,
    this.showCameraControls = false,
    this.currentZoom = 1.0,
    this.minZoom = 1.0,
    this.maxZoom = 1.0,
    required this.onZoomChanged,
    this.currentExposure = 0.0,
    required this.minExposure,
    required this.maxExposure,
    required this.onExposureChanged,
  });

  @override
  Widget build(BuildContext context) {
    final bool canZoom = maxZoom > minZoom;
    // Only show controls panel if there's something to control (either Zoom or Exposure)
    final bool hasControls = showCameraControls && (canZoom || !kIsWeb);

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 32),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.transparent,
            AppColors.background.withValues(alpha: 0.8),
            AppColors.background,
          ],
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Camera controls sliders
          if (hasControls)
            _CameraControlsSliders(
              currentZoom: currentZoom,
              minZoom: minZoom,
              maxZoom: maxZoom,
              onZoomChanged: onZoomChanged,
              currentExposure: currentExposure,
              minExposure: minExposure,
              maxExposure: maxExposure,
              onExposureChanged: onExposureChanged,
            ),
          if (hasControls) const SizedBox(height: 24),
          // Action buttons row
          if (hasImage)
            _AnalyzeButton(isLoading: isAnalyzing, onPressed: onCapturePressed)
          else
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                // Gallery button
                _ActionButton(
                  icon: Icons.photo_library_outlined,
                  label: AppLocalizations.of(context)!.galleryButton,
                  onPressed:
                      onGalleryPressed, // No need to check hasImage here as this branch is only for !hasImage
                ),
                // Shutter / Analyze button (Capture only here)
                _ShutterButton(
                  isAnalyze: false,
                  isLoading: isAnalyzing,
                  onPressed: onCapturePressed,
                ),
                // Catalog button
                _ActionButton(
                  icon: Icons.apps,
                  label: AppLocalizations.of(context)!.catalogButton,
                  onPressed: onCatalogPressed, // No need to check hasImage here
                ),
              ],
            ),
        ],
      ),
    );
  }
}

class _CameraControlsSliders extends StatelessWidget {
  final double currentZoom;
  final double minZoom;
  final double maxZoom;
  final ValueChanged<double> onZoomChanged;

  final double currentExposure;
  final double minExposure;
  final double maxExposure;
  final ValueChanged<double> onExposureChanged;

  const _CameraControlsSliders({
    required this.currentZoom,
    required this.minZoom,
    required this.maxZoom,
    required this.onZoomChanged,
    required this.currentExposure,
    required this.minExposure,
    required this.maxExposure,
    required this.onExposureChanged,
  });

  @override
  Widget build(BuildContext context) {
    final bool canZoom = maxZoom > minZoom;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface.withValues(alpha: 0.9),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.surfaceElevated),
      ),
      child: Column(
        children: [
          // ZOOM (available on all platforms IF supported)
          if (canZoom)
            _ControlSlider(
              label: AppLocalizations.of(context)!.zoomLabel,
              value: currentZoom,
              min: minZoom,
              max: maxZoom,
              displayValue: '${currentZoom.toStringAsFixed(1)}x',
              onChanged: onZoomChanged,
            ),

          if (canZoom && !kIsWeb) const SizedBox(height: 12),

          // Exposure (Hidden on Web)
          if (!kIsWeb) ...[
            _ControlSlider(
              label: AppLocalizations.of(context)!.exposureLabel,
              value: currentExposure,
              min: minExposure,
              max: maxExposure,
              displayValue: currentExposure.toStringAsFixed(1),
              onChanged: onExposureChanged,
            ),
          ],
        ],
      ),
    );
  }
}

class _ControlSlider extends StatelessWidget {
  final String label;
  final double value;
  final double min;
  final double max;
  final String displayValue;
  final ValueChanged<double> onChanged;

  const _ControlSlider({
    required this.label,
    required this.value,
    required this.min,
    required this.max,
    required this.displayValue,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(
          width: 48,
          child: Text(
            label,
            style: AppTextStyles.technical(
              fontSize: 11,
              color: AppColors.textMuted,
            ),
          ),
        ),
        Expanded(
          child: SliderTheme(
            data: SliderTheme.of(context).copyWith(
              trackHeight: 2,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
            ),
            child: Slider(
              value: value,
              min: min,
              max: max,
              onChanged: onChanged,
            ),
          ),
        ),
        SizedBox(
          width: 56,
          child: Text(
            displayValue,
            textAlign: TextAlign.right,
            style: AppTextStyles.technical(
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: AppColors.surfaceElevated),
          ),
          child: IconButton(
            icon: Icon(icon),
            iconSize: 28,
            color: AppColors.textSecondary,
            onPressed: onPressed,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          style: AppTextStyles.technical(
            fontSize: 10,
            color: AppColors.textMuted,
          ),
        ),
      ],
    );
  }
}

class _ShutterButton extends StatelessWidget {
  final bool isAnalyze;
  final bool isLoading;
  final VoidCallback onPressed;

  const _ShutterButton({
    required this.isAnalyze,
    required this.isLoading,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        GestureDetector(
          onTap: isLoading ? null : onPressed,
          child: Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: isAnalyze
                    ? [AppColors.violetAccent, const Color(0xFF9333EA)]
                    : [AppColors.cyanAccent, const Color(0xFF00B8D9)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              boxShadow: [
                BoxShadow(
                  color:
                      (isAnalyze
                              ? AppColors.violetAccent
                              : AppColors.cyanAccent)
                          .withValues(alpha: 0.4),
                  blurRadius: 20,
                  spreadRadius: 2,
                ),
              ],
            ),
            child: isLoading
                ? const Center(
                    child: SizedBox(
                      width: 28,
                      height: 28,
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 3,
                      ),
                    ),
                  )
                : isAnalyze
                ? const Icon(Icons.auto_awesome, color: Colors.white, size: 32)
                : Container(
                    margin: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.background, width: 3),
                    ),
                  ),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          isAnalyze
              ? AppLocalizations.of(context)!.analyzeLabel
              : AppLocalizations.of(context)!.captureLabel,
          style: AppTextStyles.technical(
            fontSize: 10,
            color: AppColors.textMuted,
          ),
        ),
      ],
    );
  }
}

/// Bottom sheet showing reference catalog images.
class _CatalogBottomSheet extends StatelessWidget {
  final void Function(String asset, String name) onSelect;

  const _CatalogBottomSheet({required this.onSelect});

  // Sample catalog items - these would come from assets in production
  static const _catalogItems = [
    _CatalogItem(
      name: 'Orion Nebula',
      description: 'M42 - The Great Orion Nebula',
      assetPath: 'orion_nebula',
    ),
    _CatalogItem(
      name: 'Crab Nebula',
      description: 'M1 - Supernova Remnant',
      assetPath: 'crab_nebula',
    ),
    _CatalogItem(
      name: 'Sombrero Galaxy',
      description: 'M104 - Spiral Galaxy',
      assetPath: 'hat_galaxy',
    ),
    _CatalogItem(
      name: 'Hercules Cluster',
      description: 'M13 - Globular Cluster',
      assetPath: 'hercules_cluster',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.6,
      minChildSize: 0.3,
      maxChildSize: 0.9,
      expand: false,
      builder: (context, scrollController) => Column(
        children: [
          // Handle bar
          Container(
            margin: const EdgeInsets.symmetric(vertical: 12),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.textMuted,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          // Title
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              children: [
                const Icon(Icons.auto_awesome, color: AppColors.cyanAccent),
                const SizedBox(width: 12),
                Text(
                  AppLocalizations.of(context)!.referenceCatalog,
                  style: AppTextStyles.headline(fontSize: 20),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Text(
              AppLocalizations.of(context)!.selectSampleImage,
              style: AppTextStyles.body(color: AppColors.textSecondary),
            ),
          ),
          const SizedBox(height: 16),
          // Catalog grid
          Expanded(
            child: GridView.builder(
              controller: scrollController,
              padding: const EdgeInsets.all(16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 1.0,
              ),
              itemCount: _catalogItems.length,
              itemBuilder: (context, index) {
                final item = _catalogItems[index];
                return _CatalogCard(
                  item: item,
                  onTap: () => onSelect(item.assetPath, item.name),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _CatalogItem {
  final String name;
  final String description;
  final String assetPath;

  const _CatalogItem({
    required this.name,
    required this.description,
    required this.assetPath,
  });
}

class _CatalogCard extends StatelessWidget {
  final _CatalogItem item;
  final VoidCallback onTap;

  const _CatalogCard({required this.item, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.surfaceElevated,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.surface),
          image: DecorationImage(
            image: AssetImage('assets/catalog/${item.assetPath}.gif'),
            fit: BoxFit.cover,
            onError: (_, __) {}, // Gracefully handle errors if any
          ),
        ),
        clipBehavior: Clip.antiAlias, // Ensure background image is clipped
        child: Stack(
          children: [
            // Dark gradient overlay for text readability
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.transparent,
                      Colors.black.withValues(alpha: 0.8),
                    ],
                    stops: const [0.4, 1.0],
                  ),
                ),
              ),
            ),
            // Content
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    item.name,
                    style: AppTextStyles.label(fontWeight: FontWeight.w600)
                        .copyWith(
                          color: Colors.white,
                          shadows: [
                            const Shadow(
                              offset: Offset(0, 1),
                              blurRadius: 2,
                              color: Colors.black,
                            ),
                          ],
                        ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    item.description,
                    style: AppTextStyles.technical(
                      fontSize: 10,
                      color: Colors.white.withValues(alpha: 0.8),
                    ),
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AnalyzeButton extends StatefulWidget {
  final bool isLoading;
  final VoidCallback onPressed;

  const _AnalyzeButton({required this.isLoading, required this.onPressed});

  @override
  State<_AnalyzeButton> createState() => _AnalyzeButtonState();
}

class _AnalyzeButtonState extends State<_AnalyzeButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _glowAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 1.02,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));

    _glowAnimation = Tween<double>(
      begin: 0.4,
      end: 0.8,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Transform.scale(
          scale: _scaleAnimation.value,
          child: Container(
            width: double.infinity,
            height: 64,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(32),
              gradient: const LinearGradient(
                colors: [AppColors.violetAccent, Color(0xFF9333EA)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              boxShadow: [
                BoxShadow(
                  color: AppColors.violetAccent.withValues(
                    alpha: _glowAnimation.value,
                  ),
                  blurRadius: 16 + (8 * _controller.value),
                  spreadRadius: 2 + (2 * _controller.value),
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: widget.isLoading ? null : widget.onPressed,
                borderRadius: BorderRadius.circular(32),
                child: Center(
                  child: widget.isLoading
                      ? const SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2.5,
                          ),
                        )
                      : Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.auto_awesome,
                              color: Colors.white,
                              size: 24,
                            ),
                            const SizedBox(width: 12),
                            Text(
                              AppLocalizations.of(
                                context,
                              )!.analyzeWithAi.toUpperCase(),
                              style:
                                  AppTextStyles.label(
                                    fontWeight: FontWeight.bold,
                                  ).copyWith(
                                    color: Colors.white,
                                    fontSize: 16,
                                    letterSpacing: 1.2,
                                  ),
                            ),
                          ],
                        ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
