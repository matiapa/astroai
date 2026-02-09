import 'package:json_annotation/json_annotation.dart';

part 'analysis_result.g.dart';

/// Enum representing the current step of the analysis process.
enum AnalysisStep {
  analyzingImage,
  analysisComplete,
  generatingNarration,
  narrationComplete,
  generatingAudio,
  finished,
}

/// Complete response from the `/analyze` endpoint.
@JsonSerializable(fieldRename: FieldRename.snake)
class AnalysisResult {
  /// Unique identifier for this analysis result.
  @JsonKey(includeIfNull: false)
  final String? uid;

  /// Whether the analysis was successful.
  final bool success;

  /// Plate solving data with celestial coordinates.
  final PlateSolving? plateSolving;

  /// AI-generated narration for this sky view.
  final Narration? narration;

  /// List of identified celestial objects.
  final List<IdentifiedObject> identifiedObjects;

  /// Error message if analysis failed.
  final String? error;

  const AnalysisResult({
    this.uid,
    required this.success,
    this.plateSolving,
    this.narration,
    this.identifiedObjects = const [],
    this.error,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) =>
      _$AnalysisResultFromJson(json);

  Map<String, dynamic> toJson() => _$AnalysisResultToJson(this);

  /// Creates a copy with the given fields replaced.
  AnalysisResult copyWith({
    String? uid,
    bool? success,
    PlateSolving? plateSolving,
    Narration? narration,
    List<IdentifiedObject>? identifiedObjects,
    String? error,
  }) {
    return AnalysisResult(
      uid: uid ?? this.uid,
      success: success ?? this.success,
      plateSolving: plateSolving ?? this.plateSolving,
      narration: narration ?? this.narration,
      identifiedObjects: identifiedObjects ?? this.identifiedObjects,
      error: error ?? this.error,
    );
  }
}

/// Plate solving results containing celestial coordinates.
@JsonSerializable(fieldRename: FieldRename.snake)
class PlateSolving {
  /// Right ascension of image center in degrees.
  final double centerRaDeg;

  /// Declination of image center in degrees.
  final double centerDecDeg;

  /// Image scale in arcseconds per pixel.
  final double pixelScaleArcsec;

  const PlateSolving({
    required this.centerRaDeg,
    required this.centerDecDeg,
    required this.pixelScaleArcsec,
  });

  factory PlateSolving.fromJson(Map<String, dynamic> json) =>
      _$PlateSolvingFromJson(json);

  Map<String, dynamic> toJson() => _$PlateSolvingToJson(this);
}

/// AI-generated narration for this sky view.
@JsonSerializable(fieldRename: FieldRename.snake)
class Narration {
  /// Title describing this view (Spanish).
  final String title;

  /// Full narration text (Spanish).
  final String text;

  /// URL to the audio narration WAV file (null while audio is being generated).
  final String? audioUrl;

  const Narration({required this.title, required this.text, this.audioUrl});

  /// Creates a copy with the given fields replaced.
  Narration copyWith({String? title, String? text, String? audioUrl}) {
    return Narration(
      title: title ?? this.title,
      text: text ?? this.text,
      audioUrl: audioUrl ?? this.audioUrl,
    );
  }

  factory Narration.fromJson(Map<String, dynamic> json) =>
      _$NarrationFromJson(json);

  Map<String, dynamic> toJson() => _$NarrationToJson(this);
}

/// A celestial object identified in the sky image.
@JsonSerializable(fieldRename: FieldRename.snake)
class IdentifiedObject {
  /// Catalog name of the object.
  final String name;

  /// Primary type: "Star", "Galaxy", "Nebula", "Cluster".
  final String type;

  /// Subtype: "Y*O", "Pulsating Variable Star", "Orion Variable Star", etc.
  final String? subtype;

  /// Visual (apparent) magnitude.
  final double? magnitudeVisual;

  /// B-V color index.
  final double? bvColorIndex;

  /// Spectral classification: "M3.2", "A5IV", "B3/5V", etc.
  final String? spectralType;

  /// Morphological type for galaxies: "Sb", "E0", etc.
  final String? morphologicalType;

  /// Distance in light-years.
  final double? distanceLightyears;

  /// Alternative designations.
  final List<String>? alternativeNames;

  /// Celestial coordinates (RA/Dec).
  final CelestialCoords celestialCoords;

  /// Pixel coordinates in the source image.
  final PixelCoords pixelCoords;

  /// Brief description/legend (Spanish), if available.
  final String? legend;

  const IdentifiedObject({
    required this.name,
    required this.type,
    this.subtype,
    this.magnitudeVisual,
    this.bvColorIndex,
    this.spectralType,
    this.morphologicalType,
    this.distanceLightyears,
    this.alternativeNames,
    required this.celestialCoords,
    required this.pixelCoords,
    this.legend,
  });

  factory IdentifiedObject.fromJson(Map<String, dynamic> json) =>
      _$IdentifiedObjectFromJson(json);

  Map<String, dynamic> toJson() => _$IdentifiedObjectToJson(this);

  /// Returns a human-readable distance string.
  String get distanceFormatted {
    if (distanceLightyears == null) return 'Desconocida';
    if (distanceLightyears! < 1) {
      return '${(distanceLightyears! * 365.25).toStringAsFixed(1)} días luz';
    }
    return '${distanceLightyears!.toStringAsFixed(1)} años luz';
  }

  /// Returns the display name (cleaned up).
  String get displayName {
    // Remove leading catalog prefixes like "* ", "HD ", etc. for display
    final cleaned = name.replaceFirst(RegExp(r'^\*\s*'), '');
    return cleaned.trim();
  }
}

/// Celestial coordinates in right ascension and declination.
@JsonSerializable(fieldRename: FieldRename.snake)
class CelestialCoords {
  /// Right ascension in degrees.
  final double raDeg;

  /// Declination in degrees.
  final double decDeg;

  /// Object radius in arcseconds.
  final double radiusArcsec;

  const CelestialCoords({
    required this.raDeg,
    required this.decDeg,
    required this.radiusArcsec,
  });

  factory CelestialCoords.fromJson(Map<String, dynamic> json) =>
      _$CelestialCoordsFromJson(json);

  Map<String, dynamic> toJson() => _$CelestialCoordsToJson(this);

  /// Formats RA as hours:minutes:seconds (HMS).
  String get raFormatted {
    final hours = raDeg / 15;
    final h = hours.floor();
    final m = ((hours - h) * 60).floor();
    final s = ((hours - h - m / 60) * 3600).toStringAsFixed(1);
    return '${h}h ${m}m ${s}s';
  }

  /// Formats Dec as degrees:arcminutes:arcseconds (DMS).
  String get decFormatted {
    final sign = decDeg >= 0 ? '+' : '-';
    final absDec = decDeg.abs();
    final d = absDec.floor();
    final m = ((absDec - d) * 60).floor();
    final s = ((absDec - d - m / 60) * 3600).toStringAsFixed(1);
    return "$sign$d° $m' $s\"";
  }
}

/// Pixel coordinates in the analyzed image.
@JsonSerializable(fieldRename: FieldRename.snake)
class PixelCoords {
  /// X position in pixels.
  final double x;

  /// Y position in pixels.
  final double y;

  /// Object radius in pixels (for display).
  final double radiusPixels;

  const PixelCoords({
    required this.x,
    required this.y,
    required this.radiusPixels,
  });

  factory PixelCoords.fromJson(Map<String, dynamic> json) =>
      _$PixelCoordsFromJson(json);

  Map<String, dynamic> toJson() => _$PixelCoordsToJson(this);
}
