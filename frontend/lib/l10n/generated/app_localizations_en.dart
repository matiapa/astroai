// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get settingsTitle => 'Settings';

  @override
  String get appTitle => 'AstroGuide';

  @override
  String get settingsPlaybackSection => 'PLAYBACK';

  @override
  String get settingsAutoPlay => 'Auto-play narration';

  @override
  String get settingsAutoPlaySubtitle =>
      'Automatically play audio after analysis';

  @override
  String get settingsLanguageSection => 'LANGUAGE';

  @override
  String get settingsLanguage => 'Language';

  @override
  String get settingsLanguageEn => 'English';

  @override
  String get settingsLanguageEs => 'Español';

  @override
  String get settingsAboutSection => 'ABOUT';

  @override
  String settingsVersion(String version) {
    return 'Version $version';
  }

  @override
  String get settingsOpenSourceLicenses => 'Open source licenses';

  @override
  String analysisFailed(Object error) {
    return 'Analysis failed: $error';
  }

  @override
  String get analyzingCosmos => 'Analyzing Cosmos';

  @override
  String get consultingArchives => 'Consulting Archives';

  @override
  String get synthesizingVoice => 'Synthesizing Voice';

  @override
  String get discoveryComplete => 'Discovery Complete';

  @override
  String get processing => 'Processing...';

  @override
  String get identifyingCelestialObjects =>
      'Identifying stars, nebulae, and galaxies...';

  @override
  String get craftingStory => 'Crafting a story for your discovery...';

  @override
  String get preparingAudioGuide => 'Preparing your audio guide...';

  @override
  String get preparingResults => 'Preparing results...';

  @override
  String get pleaseWait => 'Please wait...';

  @override
  String assetNotFound(Object assetPath) {
    return 'Asset not found: $assetPath';
  }

  @override
  String errorPickingImage(Object error) {
    return 'Error picking image: $error';
  }

  @override
  String captureError(Object error) {
    return 'Capture error: $error';
  }

  @override
  String cameraNotAvailable(Object error) {
    return 'Camera not available: $error';
  }

  @override
  String get openingCamera => 'Opening Camera...';

  @override
  String get loadingCamera => 'Loading Camera...';

  @override
  String get orSelectFromGalleryCatalog => 'Or select from gallery / catalog';

  @override
  String get zoomLabel => 'ZOOM';

  @override
  String get exposureLabel => 'EXP';

  @override
  String get galleryButton => 'Gallery';

  @override
  String get catalogButton => 'Catalog';

  @override
  String get noAnalysisDataFound => 'No analysis data found';

  @override
  String get returnToObservatory => 'Return to Observatory';

  @override
  String get generatingAudioStatus => 'GENERATING AUDIO...';

  @override
  String get analysisCompleteStatus => 'ANALYSIS COMPLETE';

  @override
  String get askAboutThisView => 'Ask about this view';

  @override
  String get tapForDetails => 'Tap for details';

  @override
  String get viewLess => 'View less';

  @override
  String get viewMore => 'View more';

  @override
  String get coordinatesLabel => 'Coordinates';

  @override
  String get distanceLabel => 'Distance';

  @override
  String get magnitudeLabel => 'Magnitude';

  @override
  String get spectralTypeLabel => 'Spectral Type';

  @override
  String get morphologyLabel => 'Morphology';

  @override
  String get alsoKnownAsLabel => 'Also Known As';

  @override
  String get generatingAudioTitle => 'GENERATING AUDIO';

  @override
  String get audioNarrationPending =>
      'Audio narration will appear here shortly';

  @override
  String audioLoadError(Object error) {
    return 'Could not load audio: $error';
  }

  @override
  String get navObservatory => 'Observatory';

  @override
  String get navLog => 'Log';

  @override
  String get navSettings => 'Settings';

  @override
  String get logbookTitle => 'My Discoveries';

  @override
  String get logbookSearchHint => 'Scan for objects...';

  @override
  String get logbookEmpty => 'No discoveries yet';

  @override
  String get logbookNoResults => 'No matching discoveries';

  @override
  String get logbookEmptyHint => 'Capture your first sky image to begin';

  @override
  String get logbookNoResultsHint => 'Try a different search term';

  @override
  String get goToObservatory => 'Go to Observatory';

  @override
  String get chatBotName => 'Astro-Guide 9000';

  @override
  String get comingSoon => 'Coming Soon';

  @override
  String get chatFeatureComingSoon => 'Chat Feature Coming Soon';

  @override
  String get chatFutureUpdate =>
      'The AI-powered chat assistant will be available in a future update.';

  @override
  String get referenceCatalog => 'Reference Catalog';

  @override
  String get selectSampleImage => 'Select a sample image to analyze';

  @override
  String get captureLabel => 'Capture';

  @override
  String get analyzeWithAi => 'Analyze with AI';

  @override
  String get analyzeLabel => 'Analyze';

  @override
  String get deleteLogTitle => 'Delete Log';

  @override
  String get deleteLogMessage =>
      'Are you sure you want to delete this log? This action cannot be undone.';

  @override
  String get cancelButton => 'Cancel';

  @override
  String get deleteButton => 'Delete';

  @override
  String get navChat => 'Atlas';

  @override
  String get chatAtlasTitle => 'Atlas';

  @override
  String get chatWelcomeMessage =>
      'Hello! I\'m Atlas, your astronomy guide. Ask me anything about the night sky, constellations, planets, or celestial events.';

  @override
  String get chatSuggestion1 => 'What constellations are visible tonight?';

  @override
  String get chatSuggestion2 => 'Tell me about the Orion Nebula';

  @override
  String get chatSuggestion3 => 'How can I photograph the Milky Way?';

  @override
  String get chatResultsWelcome =>
      'I have context about your sky analysis. Ask me anything about the objects identified in your image!';

  @override
  String get goBack => 'Go back';
}
