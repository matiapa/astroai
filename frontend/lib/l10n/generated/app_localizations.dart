import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('es'),
  ];

  /// Title of the settings screen
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settingsTitle;

  /// The name of the application
  ///
  /// In en, this message translates to:
  /// **'AstroGuide'**
  String get appTitle;

  /// Header for the playback settings section
  ///
  /// In en, this message translates to:
  /// **'PLAYBACK'**
  String get settingsPlaybackSection;

  /// Label for auto-play toggle
  ///
  /// In en, this message translates to:
  /// **'Auto-play narration'**
  String get settingsAutoPlay;

  /// Subtitle for auto-play toggle
  ///
  /// In en, this message translates to:
  /// **'Automatically play audio after analysis'**
  String get settingsAutoPlaySubtitle;

  /// Header for the language settings section
  ///
  /// In en, this message translates to:
  /// **'LANGUAGE'**
  String get settingsLanguageSection;

  /// Label for language selector
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get settingsLanguage;

  /// No description provided for @settingsLanguageEn.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get settingsLanguageEn;

  /// No description provided for @settingsLanguageEs.
  ///
  /// In en, this message translates to:
  /// **'Español'**
  String get settingsLanguageEs;

  /// Header for the about settings section
  ///
  /// In en, this message translates to:
  /// **'ABOUT'**
  String get settingsAboutSection;

  /// Version display
  ///
  /// In en, this message translates to:
  /// **'Version {version}'**
  String settingsVersion(String version);

  /// Label for open source licenses link
  ///
  /// In en, this message translates to:
  /// **'Open source licenses'**
  String get settingsOpenSourceLicenses;

  /// No description provided for @analysisFailed.
  ///
  /// In en, this message translates to:
  /// **'Analysis failed: {error}'**
  String analysisFailed(Object error);

  /// No description provided for @analyzingCosmos.
  ///
  /// In en, this message translates to:
  /// **'Analyzing Cosmos'**
  String get analyzingCosmos;

  /// No description provided for @consultingArchives.
  ///
  /// In en, this message translates to:
  /// **'Consulting Archives'**
  String get consultingArchives;

  /// No description provided for @synthesizingVoice.
  ///
  /// In en, this message translates to:
  /// **'Synthesizing Voice'**
  String get synthesizingVoice;

  /// No description provided for @discoveryComplete.
  ///
  /// In en, this message translates to:
  /// **'Discovery Complete'**
  String get discoveryComplete;

  /// No description provided for @processing.
  ///
  /// In en, this message translates to:
  /// **'Processing...'**
  String get processing;

  /// No description provided for @identifyingCelestialObjects.
  ///
  /// In en, this message translates to:
  /// **'Identifying stars, nebulae, and galaxies...'**
  String get identifyingCelestialObjects;

  /// No description provided for @craftingStory.
  ///
  /// In en, this message translates to:
  /// **'Crafting a story for your discovery...'**
  String get craftingStory;

  /// No description provided for @preparingAudioGuide.
  ///
  /// In en, this message translates to:
  /// **'Preparing your audio guide...'**
  String get preparingAudioGuide;

  /// No description provided for @preparingResults.
  ///
  /// In en, this message translates to:
  /// **'Preparing results...'**
  String get preparingResults;

  /// No description provided for @pleaseWait.
  ///
  /// In en, this message translates to:
  /// **'Please wait...'**
  String get pleaseWait;

  /// No description provided for @assetNotFound.
  ///
  /// In en, this message translates to:
  /// **'Asset not found: {assetPath}'**
  String assetNotFound(Object assetPath);

  /// No description provided for @errorPickingImage.
  ///
  /// In en, this message translates to:
  /// **'Error picking image: {error}'**
  String errorPickingImage(Object error);

  /// No description provided for @captureError.
  ///
  /// In en, this message translates to:
  /// **'Capture error: {error}'**
  String captureError(Object error);

  /// No description provided for @cameraNotAvailable.
  ///
  /// In en, this message translates to:
  /// **'Camera not available: {error}'**
  String cameraNotAvailable(Object error);

  /// No description provided for @openingCamera.
  ///
  /// In en, this message translates to:
  /// **'Opening Camera...'**
  String get openingCamera;

  /// No description provided for @loadingCamera.
  ///
  /// In en, this message translates to:
  /// **'Loading Camera...'**
  String get loadingCamera;

  /// No description provided for @orSelectFromGalleryCatalog.
  ///
  /// In en, this message translates to:
  /// **'Or select from gallery / catalog'**
  String get orSelectFromGalleryCatalog;

  /// No description provided for @zoomLabel.
  ///
  /// In en, this message translates to:
  /// **'ZOOM'**
  String get zoomLabel;

  /// No description provided for @exposureLabel.
  ///
  /// In en, this message translates to:
  /// **'EXP'**
  String get exposureLabel;

  /// No description provided for @galleryButton.
  ///
  /// In en, this message translates to:
  /// **'Gallery'**
  String get galleryButton;

  /// No description provided for @catalogButton.
  ///
  /// In en, this message translates to:
  /// **'Catalog'**
  String get catalogButton;

  /// No description provided for @noAnalysisDataFound.
  ///
  /// In en, this message translates to:
  /// **'No analysis data found'**
  String get noAnalysisDataFound;

  /// No description provided for @returnToObservatory.
  ///
  /// In en, this message translates to:
  /// **'Return to Observatory'**
  String get returnToObservatory;

  /// No description provided for @generatingAudioStatus.
  ///
  /// In en, this message translates to:
  /// **'GENERATING AUDIO...'**
  String get generatingAudioStatus;

  /// No description provided for @analysisCompleteStatus.
  ///
  /// In en, this message translates to:
  /// **'ANALYSIS COMPLETE'**
  String get analysisCompleteStatus;

  /// No description provided for @askAboutThisView.
  ///
  /// In en, this message translates to:
  /// **'Ask about this view'**
  String get askAboutThisView;

  /// No description provided for @tapForDetails.
  ///
  /// In en, this message translates to:
  /// **'Tap for details'**
  String get tapForDetails;

  /// No description provided for @viewLess.
  ///
  /// In en, this message translates to:
  /// **'View less'**
  String get viewLess;

  /// No description provided for @viewMore.
  ///
  /// In en, this message translates to:
  /// **'View more'**
  String get viewMore;

  /// No description provided for @coordinatesLabel.
  ///
  /// In en, this message translates to:
  /// **'Coordinates'**
  String get coordinatesLabel;

  /// No description provided for @distanceLabel.
  ///
  /// In en, this message translates to:
  /// **'Distance'**
  String get distanceLabel;

  /// No description provided for @magnitudeLabel.
  ///
  /// In en, this message translates to:
  /// **'Magnitude'**
  String get magnitudeLabel;

  /// No description provided for @spectralTypeLabel.
  ///
  /// In en, this message translates to:
  /// **'Spectral Type'**
  String get spectralTypeLabel;

  /// No description provided for @morphologyLabel.
  ///
  /// In en, this message translates to:
  /// **'Morphology'**
  String get morphologyLabel;

  /// No description provided for @alsoKnownAsLabel.
  ///
  /// In en, this message translates to:
  /// **'Also Known As'**
  String get alsoKnownAsLabel;

  /// No description provided for @generatingAudioTitle.
  ///
  /// In en, this message translates to:
  /// **'GENERATING AUDIO'**
  String get generatingAudioTitle;

  /// No description provided for @audioNarrationPending.
  ///
  /// In en, this message translates to:
  /// **'Audio narration will appear here shortly'**
  String get audioNarrationPending;

  /// No description provided for @audioLoadError.
  ///
  /// In en, this message translates to:
  /// **'Could not load audio: {error}'**
  String audioLoadError(Object error);

  /// No description provided for @navObservatory.
  ///
  /// In en, this message translates to:
  /// **'Observatory'**
  String get navObservatory;

  /// No description provided for @navLog.
  ///
  /// In en, this message translates to:
  /// **'Log'**
  String get navLog;

  /// No description provided for @navSettings.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get navSettings;

  /// No description provided for @logbookTitle.
  ///
  /// In en, this message translates to:
  /// **'My Discoveries'**
  String get logbookTitle;

  /// No description provided for @logbookSearchHint.
  ///
  /// In en, this message translates to:
  /// **'Scan for objects...'**
  String get logbookSearchHint;

  /// No description provided for @logbookEmpty.
  ///
  /// In en, this message translates to:
  /// **'No discoveries yet'**
  String get logbookEmpty;

  /// No description provided for @logbookNoResults.
  ///
  /// In en, this message translates to:
  /// **'No matching discoveries'**
  String get logbookNoResults;

  /// No description provided for @logbookEmptyHint.
  ///
  /// In en, this message translates to:
  /// **'Capture your first sky image to begin'**
  String get logbookEmptyHint;

  /// No description provided for @logbookNoResultsHint.
  ///
  /// In en, this message translates to:
  /// **'Try a different search term'**
  String get logbookNoResultsHint;

  /// No description provided for @goToObservatory.
  ///
  /// In en, this message translates to:
  /// **'Go to Observatory'**
  String get goToObservatory;

  /// No description provided for @chatBotName.
  ///
  /// In en, this message translates to:
  /// **'Astro-Guide 9000'**
  String get chatBotName;

  /// No description provided for @comingSoon.
  ///
  /// In en, this message translates to:
  /// **'Coming Soon'**
  String get comingSoon;

  /// No description provided for @chatFeatureComingSoon.
  ///
  /// In en, this message translates to:
  /// **'Chat Feature Coming Soon'**
  String get chatFeatureComingSoon;

  /// No description provided for @chatFutureUpdate.
  ///
  /// In en, this message translates to:
  /// **'The AI-powered chat assistant will be available in a future update.'**
  String get chatFutureUpdate;

  /// No description provided for @referenceCatalog.
  ///
  /// In en, this message translates to:
  /// **'Reference Catalog'**
  String get referenceCatalog;

  /// No description provided for @selectSampleImage.
  ///
  /// In en, this message translates to:
  /// **'Select a sample image to analyze'**
  String get selectSampleImage;

  /// No description provided for @captureLabel.
  ///
  /// In en, this message translates to:
  /// **'Capture'**
  String get captureLabel;

  /// No description provided for @analyzeWithAi.
  ///
  /// In en, this message translates to:
  /// **'Analyze with AI'**
  String get analyzeWithAi;

  /// No description provided for @analyzeLabel.
  ///
  /// In en, this message translates to:
  /// **'Analyze'**
  String get analyzeLabel;

  /// No description provided for @deleteLogTitle.
  ///
  /// In en, this message translates to:
  /// **'Delete Log'**
  String get deleteLogTitle;

  /// No description provided for @deleteLogMessage.
  ///
  /// In en, this message translates to:
  /// **'Are you sure you want to delete this log? This action cannot be undone.'**
  String get deleteLogMessage;

  /// No description provided for @cancelButton.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancelButton;

  /// No description provided for @deleteButton.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get deleteButton;

  /// Label for the chat tab in the navigation bar
  ///
  /// In en, this message translates to:
  /// **'Atlas'**
  String get navChat;

  /// Title shown in the chat app bar
  ///
  /// In en, this message translates to:
  /// **'Atlas'**
  String get chatAtlasTitle;

  /// Welcome message shown when the main chat is empty
  ///
  /// In en, this message translates to:
  /// **'Hello! I\'m Atlas, your astronomy guide. Ask me anything about the night sky, constellations, planets, or celestial events.'**
  String get chatWelcomeMessage;

  /// First suggested chat prompt
  ///
  /// In en, this message translates to:
  /// **'What constellations are visible tonight?'**
  String get chatSuggestion1;

  /// Second suggested chat prompt
  ///
  /// In en, this message translates to:
  /// **'Tell me about the Orion Nebula'**
  String get chatSuggestion2;

  /// Third suggested chat prompt
  ///
  /// In en, this message translates to:
  /// **'How can I photograph the Milky Way?'**
  String get chatSuggestion3;

  /// Welcome message shown in the results chat screen
  ///
  /// In en, this message translates to:
  /// **'I have context about your sky analysis. Ask me anything about the objects identified in your image!'**
  String get chatResultsWelcome;

  /// Generic go back button label
  ///
  /// In en, this message translates to:
  /// **'Go back'**
  String get goBack;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'es'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
