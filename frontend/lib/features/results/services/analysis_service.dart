import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:image_picker/image_picker.dart';
import 'package:astro_guide/core/config/app_config.dart';
import 'package:astro_guide/features/results/models/analysis_result.dart';
import 'package:astro_guide/features/results/services/analysis_service_web.dart'
    if (dart.library.io) 'package:astro_guide/features/results/services/analysis_service_stub.dart';

/// Service for communicating with the analyze API.
class AnalysisService {
  final Dio _dio;
  final String _baseUrl;

  /// Creates an analysis service.
  ///
  /// Uses [AppConfig.apiBaseUrl] by default, or provide a custom [baseUrl].
  AnalysisService({String? baseUrl, Dio? dio})
    : _baseUrl = baseUrl ?? AppConfig.apiBaseUrl,
      _dio = dio ?? Dio();

  /// Analyzes a sky image returning a stream of progress and final result.
  Stream<dynamic> analyzeImageStream(
    XFile imageFile,
    String languageCode,
  ) async* {
    try {
      final bytes = await imageFile.readAsBytes();
      yield* analyzeImageBytesStream(bytes, imageFile.name, languageCode);
    } catch (e) {
      throw Exception('Failed to read image file: $e');
    }
  }

  /// Analyzes an image from bytes as a stream.
  ///
  /// Yields progressive results as they become available:
  /// - [AnalysisStep] for progress indicators
  /// - [AnalysisResult] as partial results accumulate
  Stream<dynamic> analyzeImageBytesStream(
    List<int> bytes,
    String filename,
    String languageCode,
  ) async* {
    // Use web-specific SSE streaming on web platform for proper real-time updates
    if (kIsWeb) {
      yield* analyzeImageStreamWeb(
        '$_baseUrl/analyze',
        bytes,
        filename,
        languageCode,
      );
      return;
    }

    // Native platform implementation using Dio
    try {
      final formData = FormData.fromMap({
        'image': MultipartFile.fromBytes(bytes, filename: filename),
        'language': languageCode,
      });

      final response = await _dio.post(
        '$_baseUrl/analyze',
        data: formData,
        options: Options(
          responseType: ResponseType.stream,
          headers: {'Accept': 'text/event-stream'},
          sendTimeout: const Duration(seconds: 30),
          receiveTimeout: const Duration(seconds: 120),
        ),
      );

      final stream = (response.data.stream as Stream)
          .cast<List<int>>()
          .transform(utf8.decoder)
          .transform(const LineSplitter());

      // State for accumulating partial results
      AnalysisResult? currentResult;
      String? currentEvent;
      StringBuffer dataBuffer = StringBuffer();

      await for (final line in stream) {
        if (line.startsWith('event:')) {
          currentEvent = line.substring(6).trim();
        } else if (line.startsWith('data:')) {
          dataBuffer.write(line.substring(5).trim());
        } else if (line.isEmpty && currentEvent != null) {
          // Empty line signals end of event - process it
          final dataStr = dataBuffer.toString();
          dataBuffer.clear();

          switch (currentEvent) {
            case 'analyzing_image':
              yield AnalysisStep.analyzingImage;
              break;

            case 'analysis_complete':
              if (dataStr.isNotEmpty && dataStr.startsWith('{')) {
                final json = _parseJson(dataStr);
                currentResult = AnalysisResult(
                  success: true,
                  plateSolving: json['plate_solving'] != null
                      ? PlateSolving.fromJson(json['plate_solving'])
                      : null,
                  identifiedObjects:
                      (json['identified_objects'] as List?)
                          ?.map((e) => IdentifiedObject.fromJson(e))
                          .toList() ??
                      [],
                );
                yield AnalysisStep.analysisComplete;
              }
              break;

            case 'generating_narration':
              yield AnalysisStep.generatingNarration;
              break;

            case 'narration_complete':
              if (dataStr.isNotEmpty && dataStr.startsWith('{')) {
                final json = _parseJson(dataStr);
                // Build object legends map
                final objectLegends = Map<String, String>.from(
                  json['object_legends'] ?? {},
                );

                // Update identified objects with their legends
                final updatedObjects =
                    currentResult?.identifiedObjects.map((obj) {
                      final legend =
                          objectLegends[obj.name] ??
                          objectLegends[obj.displayName];
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

                currentResult =
                    (currentResult ?? const AnalysisResult(success: true))
                        .copyWith(
                          narration: Narration(
                            title: json['title'] ?? '',
                            text: json['text'] ?? '',
                          ),
                          identifiedObjects: updatedObjects,
                        );
                yield AnalysisStep.narrationComplete;
                yield currentResult;
              }
              break;

            case 'generating_audio':
              yield AnalysisStep.generatingAudio;
              break;

            case 'audio_complete':
              if (dataStr.isNotEmpty && dataStr.startsWith('{')) {
                final json = _parseJson(dataStr);
                final audioUrl = json['audio_url'] as String?;
                final narration = currentResult?.narration;
                if (audioUrl != null && narration != null) {
                  currentResult = currentResult!.copyWith(
                    narration: narration.copyWith(audioUrl: audioUrl),
                  );
                  yield AnalysisStep.finished;
                  yield currentResult;
                }
              }
              break;

            case 'error':
              if (dataStr.isNotEmpty && dataStr.startsWith('{')) {
                final json = _parseJson(dataStr);
                throw Exception(json['error'] ?? 'Unknown error');
              }
              break;
          }
          currentEvent = null;
        }
      }
    } on DioException catch (e) {
      if (e.response != null) {
        throw Exception(
          'Analysis failed: ${e.response?.statusCode} - ${e.response?.data}',
        );
      }
      throw Exception('Connection error: ${e.message}');
    } catch (e) {
      throw Exception('Unexpected error: $e');
    }
  }

  Map<String, dynamic> _parseJson(String source) {
    return jsonDecode(source);
  }
}

/// Exception thrown when analysis fails.
class AnalysisException implements Exception {
  final String message;
  final dynamic originalError;

  AnalysisException(this.message, [this.originalError]);

  @override
  String toString() => 'AnalysisException: $message';
}
