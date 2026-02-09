// Stub for non-web platforms - web streaming not needed
Stream<dynamic> analyzeImageStreamWeb(
  String url,
  List<int> bytes,
  String filename,
  String languageCode,
) async* {
  throw UnsupportedError('Web SSE streaming is only available on web platform');
}
