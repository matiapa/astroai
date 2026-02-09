/// Application configuration loaded from compile-time environment variables.
///
/// Use `--dart-define` flags when building:
/// ```bash
/// flutter run --dart-define=API_BASE_URL=http://localhost:8000
/// flutter build apk --dart-define=API_BASE_URL=https://api.astroguide.app
/// ```
class AppConfig {
  /// Base URL for the analysis API.
  ///
  /// Set via: `--dart-define=API_BASE_URL=http://localhost:8000`
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  /// Whether to enable debug features.
  ///
  /// Set via: `--dart-define=DEBUG_MODE=true`
  static const bool debugMode = bool.fromEnvironment(
    'DEBUG_MODE',
    defaultValue: false,
  );

  /// App environment (development, staging, production).
  ///
  /// Set via: `--dart-define=ENVIRONMENT=production`
  static const String environment = String.fromEnvironment(
    'ENVIRONMENT',
    defaultValue: 'development',
  );

  /// Base URL for the A2A agent (Atlas).
  ///
  /// Set via: `--dart-define=A2A_AGENT_URL=http://localhost:10000`
  static const String a2aAgentUrl = String.fromEnvironment(
    'A2A_AGENT_URL',
    defaultValue: 'http://localhost:8000/a2a',
  );

  /// Whether running in production.
  static bool get isProduction => environment == 'production';

  /// Whether running in development.
  static bool get isDevelopment => environment == 'development';
}
