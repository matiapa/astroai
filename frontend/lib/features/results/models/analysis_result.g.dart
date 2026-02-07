// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'analysis_result.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AnalysisResult _$AnalysisResultFromJson(Map<String, dynamic> json) =>
    AnalysisResult(
      uid: json['uid'] as String?,
      success: json['success'] as bool,
      plateSolving: json['plate_solving'] == null
          ? null
          : PlateSolving.fromJson(
              json['plate_solving'] as Map<String, dynamic>,
            ),
      narration: json['narration'] == null
          ? null
          : Narration.fromJson(json['narration'] as Map<String, dynamic>),
      identifiedObjects:
          (json['identified_objects'] as List<dynamic>?)
              ?.map((e) => IdentifiedObject.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      error: json['error'] as String?,
    );

Map<String, dynamic> _$AnalysisResultToJson(AnalysisResult instance) =>
    <String, dynamic>{
      if (instance.uid case final value?) 'uid': value,
      'success': instance.success,
      'plate_solving': instance.plateSolving,
      'narration': instance.narration,
      'identified_objects': instance.identifiedObjects,
      'error': instance.error,
    };

PlateSolving _$PlateSolvingFromJson(Map<String, dynamic> json) => PlateSolving(
  centerRaDeg: (json['center_ra_deg'] as num).toDouble(),
  centerDecDeg: (json['center_dec_deg'] as num).toDouble(),
  pixelScaleArcsec: (json['pixel_scale_arcsec'] as num).toDouble(),
);

Map<String, dynamic> _$PlateSolvingToJson(PlateSolving instance) =>
    <String, dynamic>{
      'center_ra_deg': instance.centerRaDeg,
      'center_dec_deg': instance.centerDecDeg,
      'pixel_scale_arcsec': instance.pixelScaleArcsec,
    };

Narration _$NarrationFromJson(Map<String, dynamic> json) => Narration(
  title: json['title'] as String,
  text: json['text'] as String,
  audioUrl: json['audio_url'] as String?,
);

Map<String, dynamic> _$NarrationToJson(Narration instance) => <String, dynamic>{
  'title': instance.title,
  'text': instance.text,
  'audio_url': instance.audioUrl,
};

IdentifiedObject _$IdentifiedObjectFromJson(Map<String, dynamic> json) =>
    IdentifiedObject(
      name: json['name'] as String,
      type: json['type'] as String,
      subtype: json['subtype'] as String?,
      magnitudeVisual: (json['magnitude_visual'] as num?)?.toDouble(),
      bvColorIndex: (json['bv_color_index'] as num?)?.toDouble(),
      spectralType: json['spectral_type'] as String?,
      morphologicalType: json['morphological_type'] as String?,
      distanceLightyears: (json['distance_lightyears'] as num?)?.toDouble(),
      alternativeNames: (json['alternative_names'] as List<dynamic>?)?.map((e) => e as String).toList(),
      celestialCoords: CelestialCoords.fromJson(
        json['celestial_coords'] as Map<String, dynamic>,
      ),
      pixelCoords: PixelCoords.fromJson(
        json['pixel_coords'] as Map<String, dynamic>,
      ),
      legend: json['legend'] as String?,
    );

Map<String, dynamic> _$IdentifiedObjectToJson(IdentifiedObject instance) =>
    <String, dynamic>{
      'name': instance.name,
      'type': instance.type,
      'subtype': instance.subtype,
      'magnitude_visual': instance.magnitudeVisual,
      'bv_color_index': instance.bvColorIndex,
      'spectral_type': instance.spectralType,
      'morphological_type': instance.morphologicalType,
      'distance_lightyears': instance.distanceLightyears,
      'alternative_names': instance.alternativeNames,
      'celestial_coords': instance.celestialCoords,
      'pixel_coords': instance.pixelCoords,
      'legend': instance.legend,
    };

CelestialCoords _$CelestialCoordsFromJson(Map<String, dynamic> json) =>
    CelestialCoords(
      raDeg: (json['ra_deg'] as num).toDouble(),
      decDeg: (json['dec_deg'] as num).toDouble(),
      radiusArcsec: (json['radius_arcsec'] as num).toDouble(),
    );

Map<String, dynamic> _$CelestialCoordsToJson(CelestialCoords instance) =>
    <String, dynamic>{
      'ra_deg': instance.raDeg,
      'dec_deg': instance.decDeg,
      'radius_arcsec': instance.radiusArcsec,
    };

PixelCoords _$PixelCoordsFromJson(Map<String, dynamic> json) => PixelCoords(
  x: (json['x'] as num).toDouble(),
  y: (json['y'] as num).toDouble(),
  radiusPixels: (json['radius_pixels'] as num).toDouble(),
);

Map<String, dynamic> _$PixelCoordsToJson(PixelCoords instance) =>
    <String, dynamic>{
      'x': instance.x,
      'y': instance.y,
      'radius_pixels': instance.radiusPixels,
    };
