import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:uuid/uuid.dart';

import 'package:astro_guide/features/logbook/models/logbook_entry.dart';
import 'package:astro_guide/features/logbook/providers/logbook_provider.dart';
import 'package:astro_guide/features/results/models/analysis_result.dart';
import 'package:astro_guide/features/results/services/analysis_service.dart';

part 'analysis_provider.g.dart';

const _uuid = Uuid();

/// Provider for the [AnalysisService].
@riverpod
AnalysisService analysisService(Ref ref) {
  // Config is handled internally by AnalysisService's default constructor
  return AnalysisService();
}

/// Helper class to hold analysis input data (file or bytes).
class AnalysisInput {
  final XFile? file;
  final Uint8List? bytes;
  final String? filename;

  AnalysisInput.file(this.file) : bytes = null, filename = null;
  AnalysisInput.bytes(this.bytes, this.filename) : file = null;
}

/// State holding both the analysis result and the source image.
class AnalysisState {
  /// Unique ID of the current analysis (for navigation).
  final String? uid;
  final AnalysisResult? result;
  final Uint8List? imageBytes;
  final AnalysisStep? loadingStep;

  /// Whether audio generation is still in progress.
  final bool isAudioLoading;

  const AnalysisState({
    this.uid,
    this.result,
    this.imageBytes,
    this.loadingStep,
    this.isAudioLoading = false,
  });

  AnalysisState copyWith({
    String? uid,
    AnalysisResult? result,
    Uint8List? imageBytes,
    AnalysisStep? loadingStep,
    bool? isAudioLoading,
  }) {
    return AnalysisState(
      uid: uid ?? this.uid,
      result: result ?? this.result,
      imageBytes: imageBytes ?? this.imageBytes,
      loadingStep: loadingStep ?? this.loadingStep,
      isAudioLoading: isAudioLoading ?? this.isAudioLoading,
    );
  }
}

/// Provider managing the state of the current analysis.
@riverpod
class AnalysisController extends _$AnalysisController {
  @override
  AsyncValue<AnalysisState> build() {
    return const AsyncValue.data(AnalysisState());
  }

  /// Analyzes an image (file or bytes).
  Future<void> analyze(AnalysisInput input) async {
    state = const AsyncValue.loading();
    try {
      final service = ref.read(analysisServiceProvider);

      // Generate new UID for this analysis
      final analysisUid = _uuid.v4();

      // Determine display bytes first
      final Uint8List displayBytes;
      if (input.file != null) {
        displayBytes = await input.file!.readAsBytes();
      } else if (input.bytes != null) {
        displayBytes = input.bytes!;
      } else {
        throw Exception('Invalid input: No file or bytes provided');
      }

      // Initialize state with image and first step
      state = AsyncValue.data(
        AnalysisState(
          uid: analysisUid,
          imageBytes: displayBytes,
          loadingStep: AnalysisStep.analyzingImage,
        ),
      );

      final stream = input.file != null
          ? service.analyzeImageStream(input.file!)
          : service.analyzeImageBytesStream(
              input.bytes!,
              input.filename ?? 'upload.jpg',
            );

      await for (final event in stream) {
        if (event is AnalysisStep) {
          // Update loading step
          bool audioLoading = state.value?.isAudioLoading ?? false;

          // When narration completes, audio generation starts
          if (event == AnalysisStep.narrationComplete ||
              event == AnalysisStep.generatingAudio) {
            audioLoading = true;
          }
          // When finished, audio is done
          if (event == AnalysisStep.finished) {
            audioLoading = false;
          }

          state = AsyncValue.data(
            state.value!.copyWith(
              loadingStep: event,
              isAudioLoading: audioLoading,
            ),
          );
        } else if (event is AnalysisResult) {
          // Merge with existing result or use as new result
          final currentResult = state.value?.result;
          AnalysisResult mergedResult;

          if (currentResult != null) {
            // Merge: prefer new values if available, preserve UID
            mergedResult = AnalysisResult(
              uid: analysisUid,
              success: event.success,
              plateSolving: event.plateSolving ?? currentResult.plateSolving,
              narration: event.narration ?? currentResult.narration,
              identifiedObjects: event.identifiedObjects.isNotEmpty
                  ? event.identifiedObjects
                  : currentResult.identifiedObjects,
              error: event.error ?? currentResult.error,
            );
          } else {
            mergedResult = event.copyWith(uid: analysisUid);
          }

          // Determine if audio is still loading
          final isAudioLoading = mergedResult.narration?.audioUrl == null;

          state = AsyncValue.data(
            state.value!.copyWith(
              result: mergedResult,
              isAudioLoading: isAudioLoading,
            ),
          );

          // Save to logbook when narration is available (first result with content)
          if (mergedResult.narration != null && displayBytes.isNotEmpty) {
            final entry = LogbookEntry.fromAnalysis(
              uid: analysisUid,
              result: mergedResult,
              imageBytes: displayBytes,
            );
            await logbookServiceInstance.saveEntry(entry);

            // Refresh logbook entries if provider is listening
            ref.invalidate(logbookEntriesProvider);
          }
        }
      }
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  /// Loads an analysis from storage by UID.
  Future<void> loadFromUid(String uid) async {
    state = const AsyncValue.loading();
    try {
      final entry = logbookServiceInstance.getEntry(uid);
      if (entry == null) {
        state = AsyncValue.error(
          Exception('Analysis not found: $uid'),
          StackTrace.current,
        );
        return;
      }

      final result = entry.analysisResult.copyWith(uid: uid);
      state = AsyncValue.data(
        AnalysisState(
          uid: uid,
          result: result,
          imageBytes: entry.imageBytes,
          isAudioLoading: false,
        ),
      );
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  /// Resets the analysis state.
  void reset() {
    state = const AsyncValue.data(AnalysisState());
  }
}
