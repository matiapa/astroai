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
  Stream<dynamic> analyzeImageStream(XFile imageFile) async* {
    try {
      final bytes = await imageFile.readAsBytes();
      yield* analyzeImageBytesStream(bytes, imageFile.name);
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
  ) async* {
    // Check for mock data configuration
    if (AppConfig.useMockData) {
      yield* _getMockAnalysisStream();
      return;
    }

    // Use web-specific SSE streaming on web platform for proper real-time updates
    if (kIsWeb) {
      yield* analyzeImageStreamWeb('$_baseUrl/analyze', bytes, filename);
      return;
    }

    // Native platform implementation using Dio
    try {
      final formData = FormData.fromMap({
        'image': MultipartFile.fromBytes(bytes, filename: filename),
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

      final stream = (response.data.stream as Stream).cast<List<int>>()
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
                  identifiedObjects: (json['identified_objects'] as List?)
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
                final objectLegends =
                    Map<String, String>.from(json['object_legends'] ?? {});

                // Update identified objects with their legends
                final updatedObjects =
                    currentResult?.identifiedObjects.map((obj) {
                          final legend = objectLegends[obj.name] ??
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

                currentResult = (currentResult ?? const AnalysisResult(success: true))
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

  /// Mock stream generator matching progressive SSE events.
  Stream<dynamic> _getMockAnalysisStream() async* {
    // Step 1: Analyzing image
    yield AnalysisStep.analyzingImage;
    await Future.delayed(const Duration(seconds: 1));

    // Step 2: Analysis complete - yield partial result with plate solving and objects
    yield AnalysisStep.analysisComplete;
    await Future.delayed(const Duration(milliseconds: 200));

    // Step 3: Generating narration
    yield AnalysisStep.generatingNarration;
    await Future.delayed(const Duration(seconds: 1));

    // Step 4: Narration complete - yield result WITH narration but WITHOUT audio
    yield AnalysisStep.narrationComplete;
    yield _getMockNarrationResult();

    // Step 5: Generating audio (continues in background while user views results)
    yield AnalysisStep.generatingAudio;
    await Future.delayed(const Duration(seconds: 3)); // Longer delay to show loading indicator

    // Step 6: Audio complete - yield final result with audio URL
    yield AnalysisStep.finished;
    yield _getMockFinalResult();
  }

  /// Returns mock result after narration (no audio yet).
  AnalysisResult _getMockNarrationResult() {
    return AnalysisResult(
      success: true,
      plateSolving: const PlateSolving(
        centerRaDeg: 83.809927,
        centerDecDeg: -4.852231,
        pixelScaleArcsec: 5.0927,
      ),
      narration: const Narration(
        title: 'El Corazón de Orión y sus Cunas Estelares',
        text:
            'Bienvenidos a una de las regiones más dinámicas y fascinantes de nuestro cielo nocturno, situada en las inmediaciones de la espada de Orión el Cazador. Al mirar a través de este telescopio, estamos observando un auténtico laboratorio cósmico donde la vida de las estrellas comienza y evoluciona ante nuestros ojos. Lo primero que salta a la vista es la enorme diferencia de distancias; mientras que la brillante estrella 45 Orionis se encuentra a unos relativamente cercanos 372 años luz, otros objetos en el fondo, como los jóvenes objetos estelares, se sitúan a más de 1400 años luz, inmersos en las profundidades de la Gran Nebulosa de Orión. Esta profundidad visual nos permite apreciar la estructura tridimensional de nuestra galaxia en un solo vistazo.\n\nEn este campo de visión conviven estrellas veteranas con infantes estelares que apenas están despertando. Es fascinante observar a HD 36958, una estrella variable de tipo Orión que brilla con un color blanco azulado intenso debido a su altísima temperatura superficial. Cerca de ella encontramos a HD 36843, una estrella pulsante que late rítmicamente en el espacio. Pero quizás lo más asombroso sean los objetos identificados como YSOs, o estrellas jóvenes en formación. Estos astros, como el pequeño sol rojo RHS 2000 1-1048, todavía están envueltos en sus capullos de gas y polvo, recordándonos que el universo sigue creando nuevos mundos en este preciso instante, utilizando los mismos elementos que algún día formaron nuestro propio sistema solar.',
        // audioUrl is null - still generating
      ),
      identifiedObjects: _getMockIdentifiedObjects(),
    );
  }

  /// Returns final mock result with audio URL.
  AnalysisResult _getMockFinalResult() {
    return AnalysisResult(
      success: true,
      plateSolving: const PlateSolving(
        centerRaDeg: 83.809927,
        centerDecDeg: -4.852231,
        pixelScaleArcsec: 5.0927,
      ),
      narration: const Narration(
        title: 'El Corazón de Orión y sus Cunas Estelares',
        text:
            'Bienvenidos a una de las regiones más dinámicas y fascinantes de nuestro cielo nocturno, situada en las inmediaciones de la espada de Orión el Cazador. Al mirar a través de este telescopio, estamos observando un auténtico laboratorio cósmico donde la vida de las estrellas comienza y evoluciona ante nuestros ojos. Lo primero que salta a la vista es la enorme diferencia de distancias; mientras que la brillante estrella 45 Orionis se encuentra a unos relativamente cercanos 372 años luz, otros objetos en el fondo, como los jóvenes objetos estelares, se sitúan a más de 1400 años luz, inmersos en las profundidades de la Gran Nebulosa de Orión. Esta profundidad visual nos permite apreciar la estructura tridimensional de nuestra galaxia en un solo vistazo.\n\nEn este campo de visión conviven estrellas veteranas con infantes estelares que apenas están despertando. Es fascinante observar a HD 36958, una estrella variable de tipo Orión que brilla con un color blanco azulado intenso debido a su altísima temperatura superficial. Cerca de ella encontramos a HD 36843, una estrella pulsante que late rítmicamente en el espacio. Pero quizás lo más asombroso sean los objetos identificados como YSOs, o estrellas jóvenes en formación. Estos astros, como el pequeño sol rojo RHS 2000 1-1048, todavía están envueltos en sus capullos de gas y polvo, recordándonos que el universo sigue creando nuevos mundos en este preciso instante, utilizando los mismos elementos que algún día formaron nuestro propio sistema solar.',
        audioUrl: 'http://localhost:8000/audio/narration_bd841a9f.wav',
      ),
      identifiedObjects: _getMockIdentifiedObjects(),
    );
  }

  /// Returns mock identified objects list.
  List<IdentifiedObject> _getMockIdentifiedObjects() {
    return const [
      IdentifiedObject(
        name: '[RHS2000] 1-1048',
        type: 'Star',
        subtype: 'Y*O',
        magnitudeVisual: 16.06,
        spectralType: 'M3.2',
        distanceLightyears: 1455.4,
        celestialCoords: CelestialCoords(
          raDeg: 83.768188,
          decDeg: -6.014748,
          radiusArcsec: 77.04,
        ),
        pixelCoords: PixelCoords(x: 260.41, y: 287.78, radiusPixels: 15.13),
        legend:
            'Una estrella enana roja muy joven de tipo M3.2, situada a 1455 años luz, que representa las etapas iniciales de la vida estelar.',
      ),
      IdentifiedObject(
        name: '2MASS J05353092-0555423',
        type: 'Star',
        subtype: 'Y*O',
        distanceLightyears: 1307.8,
        celestialCoords: CelestialCoords(
          raDeg: 83.878874,
          decDeg: -5.928439,
          radiusArcsec: 107.93,
        ),
        pixelCoords: PixelCoords(x: 339.46, y: 302.82, radiusPixels: 21.19),
        legend:
            'Un objeto estelar joven detectado en el infrarrojo, ubicado a 1307 años luz dentro de las nubes moleculares de Orión.',
      ),
      IdentifiedObject(
        name: '*  45 Ori',
        type: 'Star',
        subtype: 'Star',
        magnitudeVisual: 5.23,
        bvColorIndex: 0.25,
        spectralType: 'A9IV/V',
        distanceLightyears: 372.1,
        celestialCoords: CelestialCoords(
          raDeg: 83.914517,
          decDeg: -4.856067,
          radiusArcsec: 62.82,
        ),
        pixelCoords: PixelCoords(x: 707.26, y: 809.82, radiusPixels: 12.33),
      ),
      IdentifiedObject(
        name: '2MASS J05352379-0450167',
        type: 'Star',
        subtype: 'Y*O',
        distanceLightyears: 1297.6,
        celestialCoords: CelestialCoords(
          raDeg: 83.849225,
          decDeg: -4.837938,
          radiusArcsec: 87.9,
        ),
        pixelCoords: PixelCoords(x: 679.1, y: 840.24, radiusPixels: 17.26),
        legend:
            'Otro infante estelar situado a 1297 años luz, cuya luz nos llega tras atravesar densas regiones de polvo cósmico.',
      ),
      IdentifiedObject(
        name: '2MASS J05344683-0534233',
        type: 'Star',
        subtype: 'Star',
        celestialCoords: CelestialCoords(
          raDeg: 83.695067,
          decDeg: -5.573322,
          radiusArcsec: 21.11,
        ),
        pixelCoords: PixelCoords(x: 368.35, y: 523.97, radiusPixels: 4.15),
        legend:
            'Una estrella catalogada por su emisión infrarroja que forma parte del rico vecindario estelar de la constelación del Cazador.',
      ),
      IdentifiedObject(
        name: 'HD  36843',
        type: 'Star',
        subtype: 'Pulsating Variable Star',
        magnitudeVisual: 6.82,
        bvColorIndex: 0.17,
        spectralType: 'A5IV',
        distanceLightyears: 487.1,
        celestialCoords: CelestialCoords(
          raDeg: 83.60034,
          decDeg: -4.804338,
          radiusArcsec: 27.11,
        ),
        pixelCoords: PixelCoords(x: 568.2, y: 936.5, radiusPixels: 5.32),
      ),
      IdentifiedObject(
        name: 'HD  36958',
        type: 'Star',
        subtype: 'Orion Variable Star',
        magnitudeVisual: 6.9,
        bvColorIndex: 0.32,
        spectralType: 'B3/5V',
        distanceLightyears: 1183.8,
        celestialCoords: CelestialCoords(
          raDeg: 83.769948,
          decDeg: -4.731841,
          radiusArcsec: 23.87,
        ),
        pixelCoords: PixelCoords(x: 675.86, y: 918.07, radiusPixels: 4.69),
      ),
    ];
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
