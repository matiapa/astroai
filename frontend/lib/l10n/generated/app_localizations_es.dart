// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get settingsTitle => 'Ajustes';

  @override
  String get appTitle => 'AstroGuía';

  @override
  String get settingsPlaybackSection => 'REPRODUCCIÓN';

  @override
  String get settingsAutoPlay => 'Reproducción automática';

  @override
  String get settingsAutoPlaySubtitle =>
      'Reproducir audio automáticamente tras análisis';

  @override
  String get settingsLanguageSection => 'IDIOMA';

  @override
  String get settingsLanguage => 'Idioma';

  @override
  String get settingsLanguageEn => 'Inglés';

  @override
  String get settingsLanguageEs => 'Español';

  @override
  String get settingsAboutSection => 'ACERCA DE';

  @override
  String settingsVersion(String version) {
    return 'Versión $version';
  }

  @override
  String get settingsOpenSourceLicenses => 'Licencias de código abierto';

  @override
  String analysisFailed(Object error) {
    return 'Error de análisis: $error';
  }

  @override
  String get analyzingCosmos => 'Analizando el Cosmos';

  @override
  String get consultingArchives => 'Consultando Archivos';

  @override
  String get synthesizingVoice => 'Sintetizando Voz';

  @override
  String get discoveryComplete => 'Descubrimiento Completo';

  @override
  String get processing => 'Procesando...';

  @override
  String get identifyingCelestialObjects =>
      'Identificando estrellas, nebulosas y galaxias...';

  @override
  String get craftingStory => 'Creando una historia para tu descubrimiento...';

  @override
  String get preparingAudioGuide => 'Preparando tu audioguía...';

  @override
  String get preparingResults => 'Preparando resultados...';

  @override
  String get pleaseWait => 'Por favor espera...';

  @override
  String assetNotFound(Object assetPath) {
    return 'Recurso no encontrado: $assetPath';
  }

  @override
  String errorPickingImage(Object error) {
    return 'Error seleccionando imagen: $error';
  }

  @override
  String captureError(Object error) {
    return 'Error de captura: $error';
  }

  @override
  String cameraNotAvailable(Object error) {
    return 'Cámara no disponible: $error';
  }

  @override
  String get openingCamera => 'Abriendo Cámara...';

  @override
  String get loadingCamera => 'Cargando Cámara...';

  @override
  String get orSelectFromGalleryCatalog => 'O selecciona de galería / catálogo';

  @override
  String get zoomLabel => 'ZOOM';

  @override
  String get exposureLabel => 'EXP';

  @override
  String get galleryButton => 'Galería';

  @override
  String get catalogButton => 'Catálogo';

  @override
  String get noAnalysisDataFound => 'No se encontraron datos de análisis';

  @override
  String get returnToObservatory => 'Volver al Observatorio';

  @override
  String get generatingAudioStatus => 'GENERANDO AUDIO...';

  @override
  String get analysisCompleteStatus => 'ANÁLISIS COMPLETO';

  @override
  String get askAboutThisView => 'Preguntar sobre esta vista';

  @override
  String get tapForDetails => 'Toca para detalles';

  @override
  String get viewLess => 'Ver menos';

  @override
  String get viewMore => 'Ver más';

  @override
  String get coordinatesLabel => 'Coordenadas';

  @override
  String get distanceLabel => 'Distancia';

  @override
  String get magnitudeLabel => 'Magnitud';

  @override
  String get spectralTypeLabel => 'Tipo Espectral';

  @override
  String get morphologyLabel => 'Morfología';

  @override
  String get alsoKnownAsLabel => 'También conocido como';

  @override
  String get generatingAudioTitle => 'GENERANDO AUDIO';

  @override
  String get audioNarrationPending => 'La narración de audio aparecerá pronto';

  @override
  String audioLoadError(Object error) {
    return 'Could not load audio: $error';
  }

  @override
  String get navObservatory => 'Observatorio';

  @override
  String get navLog => 'Bitácora';

  @override
  String get navSettings => 'Ajustes';

  @override
  String get logbookTitle => 'Mis Descubrimientos';

  @override
  String get logbookSearchHint => 'Escanear objetos...';

  @override
  String get logbookEmpty => 'Aún no hay descubrimientos';

  @override
  String get logbookNoResults => 'No hay coincidencias';

  @override
  String get logbookEmptyHint => 'Captura tu primera imagen para comenzar';

  @override
  String get logbookNoResultsHint => 'Prueba otro término de búsqueda';

  @override
  String get goToObservatory => 'Ir al Observatorio';

  @override
  String get chatBotName => 'Astro-Guide 9000';

  @override
  String get comingSoon => 'Próximamente';

  @override
  String get chatFeatureComingSoon => 'Función de Chat Próximamente';

  @override
  String get chatFutureUpdate =>
      'El asistente de chat impulsado por IA estará disponible en una actualización futura.';

  @override
  String get referenceCatalog => 'Catálogo de Referencia';

  @override
  String get selectSampleImage =>
      'Selecciona una imagen de muestra para analizar';

  @override
  String get captureLabel => 'Capturar';

  @override
  String get analyzeWithAi => 'Analizar con IA';

  @override
  String get analyzeLabel => 'Analizar';

  @override
  String get deleteLogTitle => 'Eliminar registro';

  @override
  String get deleteLogMessage =>
      '¿Estás seguro de que quieres eliminar este registro? Esta acción no se puede deshacer.';

  @override
  String get cancelButton => 'Cancelar';

  @override
  String get deleteButton => 'Eliminar';
}
