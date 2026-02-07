import 'dart:convert';
import 'dart:typed_data';

import 'package:hive_ce/hive.dart';
import 'package:astro_guide/features/results/models/analysis_result.dart';

part 'logbook_entry.g.dart';

/// A persisted entry in the user's logbook of discoveries.
///
/// Stores both the display metadata (title, thumbnail) and the full
/// analysis result for later retrieval.
@HiveType(typeId: 0)
class LogbookEntry extends HiveObject {
  /// Unique identifier for this entry.
  @HiveField(0)
  final String uid;

  /// Title from the narration, used for display.
  @HiveField(1)
  final String title;

  /// Timestamp when the analysis was completed.
  @HiveField(2)
  final DateTime timestamp;

  /// Thumbnail image bytes for the logbook grid.
  @HiveField(3)
  final Uint8List thumbnailBytes;

  /// Full image bytes for the results screen.
  @HiveField(4)
  final Uint8List imageBytes;

  /// Serialized JSON of the full AnalysisResult.
  @HiveField(5)
  final String analysisResultJson;

  LogbookEntry({
    required this.uid,
    required this.title,
    required this.timestamp,
    required this.thumbnailBytes,
    required this.imageBytes,
    required this.analysisResultJson,
  });

  /// Deserializes the stored AnalysisResult.
  AnalysisResult get analysisResult {
    final json = jsonDecode(analysisResultJson) as Map<String, dynamic>;
    return AnalysisResult.fromJson(json);
  }

  /// Creates a LogbookEntry from an AnalysisResult and image bytes.
  factory LogbookEntry.fromAnalysis({
    required String uid,
    required AnalysisResult result,
    required Uint8List imageBytes,
  }) {
    return LogbookEntry(
      uid: uid,
      title: result.narration?.title ?? 'Untitled Discovery',
      timestamp: DateTime.now(),
      thumbnailBytes: imageBytes, // For now, use full image; could resize later
      imageBytes: imageBytes,
      analysisResultJson: jsonEncode(result.toJson()),
    );
  }
}
