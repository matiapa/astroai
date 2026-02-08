import 'package:hive_ce_flutter/hive_flutter.dart';

import 'package:astro_guide/features/chat/models/chat_session.dart';

/// Service for persisting and retrieving chat sessions using Hive.
///
/// Each session stores only A2A task/context identifiers; the full
/// message history is fetched from the server on restore.
class ChatSessionService {
  static const String _boxName = 'chat_sessions';
  Box<ChatSession>? _box;

  /// Initializes the Hive box for chat session storage.
  ///
  /// Call this once during app startup after Hive.initFlutter().
  Future<void> initialize() async {
    if (!Hive.isAdapterRegistered(1)) {
      Hive.registerAdapter(ChatSessionAdapter());
    }
    _box = await Hive.openBox<ChatSession>(_boxName);
  }

  /// Ensures the box is initialized.
  Box<ChatSession> get box {
    if (_box == null) {
      throw StateError(
        'ChatSessionService not initialized. Call initialize() first.',
      );
    }
    return _box!;
  }

  /// Saves or updates a chat session.
  Future<void> saveSession(ChatSession session) async {
    await box.put(session.id, session);
  }

  /// Retrieves a single session by its local ID.
  ChatSession? getSession(String id) {
    return box.get(id);
  }

  /// Retrieves the chat session associated with a specific analysis.
  ///
  /// Returns `null` if no session exists for that analysis yet.
  ChatSession? getSessionByAnalysisId(String analysisId) {
    try {
      return box.values.firstWhere(
        (s) => s.analysisId == analysisId,
      );
    } catch (_) {
      return null;
    }
  }

  /// Returns all main-chat sessions (where [analysisId] is null),
  /// sorted newest-first by [updatedAt].
  List<ChatSession> getMainChatSessions() {
    final sessions =
        box.values.where((s) => s.analysisId == null).toList();
    sessions.sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
    return sessions;
  }

  /// Returns the most recently updated main-chat session, or `null`
  /// if no main-chat sessions exist.
  ChatSession? getLatestMainChatSession() {
    final sessions = getMainChatSessions();
    return sessions.isNotEmpty ? sessions.first : null;
  }

  /// Deletes a session by its local ID.
  Future<void> deleteSession(String id) async {
    await box.delete(id);
  }
}
