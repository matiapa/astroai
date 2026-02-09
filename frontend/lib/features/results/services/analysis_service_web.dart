// Web-specific SSE streaming implementation
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:astro_guide/features/results/models/analysis_result.dart';

/// Web-specific SSE stream for analysis using XMLHttpRequest with progress events
Stream<dynamic> analyzeImageStreamWeb(
  String url,
  List<int> bytes,
  String filename,
  String languageCode,
) {
  final controller = StreamController<dynamic>();

  final formData = html.FormData();
  final blob = html.Blob([Uint8List.fromList(bytes)]);
  formData.appendBlob('image', blob, filename);
  formData.append('language', languageCode);

  final xhr = html.HttpRequest();
  xhr.open('POST', url);
  xhr.setRequestHeader('Accept', 'text/event-stream');

  String processedText = '';
  String? currentEvent;
  String currentData = '';
  AnalysisResult? currentResult;

  void processNewData() {
    final newText = xhr.responseText ?? '';
    if (newText.length <= processedText.length) return;

    final newChunk = newText.substring(processedText.length);
    processedText = newText;

    // Process the new chunk line by line
    final lines = newChunk.split('\n');

    for (final line in lines) {
      final trimmedLine = line.trim();
      if (trimmedLine.startsWith('event:')) {
        currentEvent = trimmedLine.substring(6).trim();
      } else if (trimmedLine.startsWith('data:')) {
        currentData += trimmedLine.substring(5).trim();
      } else if (trimmedLine.isEmpty && currentEvent != null) {
        // Empty line = end of event, process it
        final eventResult = _processEvent(
          currentEvent!,
          currentData,
          currentResult,
        );

        if (eventResult != null) {
          for (final item in eventResult.items) {
            controller.add(item);
          }
          currentResult = eventResult.updatedResult;
        }

        currentEvent = null;
        currentData = '';
      }
      // Ignore comment lines starting with ':'
    }
  }

  xhr.onProgress.listen((_) {
    processNewData();
  });

  xhr.onLoad.listen((_) {
    processNewData(); // Process any remaining data
    controller.close();
  });

  xhr.onError.listen((e) {
    controller.addError(Exception('Network error during analysis'));
    controller.close();
  });

  xhr.send(formData);

  return controller.stream;
}

class _EventProcessResult {
  final List<dynamic> items;
  final AnalysisResult? updatedResult;
  _EventProcessResult(this.items, this.updatedResult);
}

_EventProcessResult? _processEvent(
  String event,
  String dataStr,
  AnalysisResult? currentResult,
) {
  final items = <dynamic>[];
  AnalysisResult? updatedResult = currentResult;

  switch (event) {
    case 'analyzing_image':
      items.add(AnalysisStep.analyzingImage);
      break;

    case 'analysis_complete':
      if (dataStr.isNotEmpty && dataStr.startsWith('{')) {
        final json = jsonDecode(dataStr);
        updatedResult = AnalysisResult(
          success: true,
          plateSolving: json['plate_solving'] != null
              ? PlateSolving.fromJson(json['plate_solving'])
              : null,
          identifiedObjects:
              (json['identified_objects'] as List?)
                  ?.map(
                    (e) => IdentifiedObject.fromJson(e as Map<String, dynamic>),
                  )
                  .toList() ??
              [],
        );
        items.add(AnalysisStep.analysisComplete);
      }
      break;

    case 'generating_narration':
      items.add(AnalysisStep.generatingNarration);
      break;

    case 'narration_complete':
      if (dataStr.isNotEmpty && dataStr.startsWith('{')) {
        final json = jsonDecode(dataStr);
        // Build object legends map
        final objectLegends = Map<String, String>.from(
          json['object_legends'] ?? {},
        );

        // Update identified objects with their legends
        final updatedObjects =
            currentResult?.identifiedObjects.map((obj) {
              final legend =
                  objectLegends[obj.name] ?? objectLegends[obj.displayName];
              if (legend != null) {
                return IdentifiedObject(
                  name: obj.name,
                  type: obj.type,
                  subtype: obj.subtype,
                  magnitudeVisual: obj.magnitudeVisual,
                  bvColorIndex: obj.bvColorIndex,
                  spectralType: obj.spectralType,
                  morphologicalType: obj.morphologicalType,
                  distanceLightyears: obj.distanceLightyears,
                  alternativeNames: obj.alternativeNames,
                  celestialCoords: obj.celestialCoords,
                  pixelCoords: obj.pixelCoords,
                  legend: legend,
                );
              }
              return obj;
            }).toList() ??
            [];

        updatedResult = (currentResult ?? const AnalysisResult(success: true))
            .copyWith(
              narration: Narration(
                title: json['title'] ?? '',
                text: json['text'] ?? '',
              ),
              identifiedObjects: updatedObjects,
            );
        items.add(AnalysisStep.narrationComplete);
        items.add(updatedResult);
      }
      break;

    case 'generating_audio':
      items.add(AnalysisStep.generatingAudio);
      break;

    case 'audio_complete':
      if (dataStr.isNotEmpty && dataStr.startsWith('{')) {
        final json = jsonDecode(dataStr);
        final audioUrl = json['audio_url'] as String?;
        final narration = currentResult?.narration;
        if (audioUrl != null && narration != null) {
          updatedResult = currentResult!.copyWith(
            narration: narration.copyWith(audioUrl: audioUrl),
          );
          items.add(AnalysisStep.finished);
          items.add(updatedResult);
        }
      }
      break;

    case 'error':
      if (dataStr.isNotEmpty && dataStr.startsWith('{')) {
        final json = jsonDecode(dataStr);
        throw Exception(json['error'] ?? 'Unknown error');
      }
      break;
  }

  if (items.isEmpty && updatedResult == currentResult) {
    return null;
  }
  return _EventProcessResult(items, updatedResult);
}
