import 'package:hive_ce/hive.dart';

part 'chat_session.g.dart';

/// A persisted chat session referencing one or more A2A tasks.
///
/// Stores the A2A identifiers needed to restore a conversation
/// from the server via `tasks/get`. A single conversation may span
/// multiple tasks (each task finishes, and the next message creates
/// a new task within the same context). [taskIds] accumulates every
/// task ID so the full history can be reconstructed.
@HiveType(typeId: 1)
class ChatSession extends HiveObject {
  /// Local unique identifier for this session.
  @HiveField(0)
  final String id;

  /// A2A server task ID of the most recent task. Null until the first
  /// message is sent and the server assigns an ID.
  @HiveField(1)
  String? taskId;

  /// A2A server context ID for grouping related tasks.
  @HiveField(2)
  String? contextId;

  /// If non-null, this session belongs to a results chat for the given
  /// analysis. Null for main (general) chat sessions.
  @HiveField(3)
  final String? analysisId;

  /// Human-readable title for display in conversation history.
  @HiveField(4)
  String title;

  /// When the session was first created.
  @HiveField(5)
  final DateTime createdAt;

  /// When the session was last updated (message sent).
  @HiveField(6)
  DateTime updatedAt;

  /// Ordered list of all A2A task IDs created within this session.
  /// A conversation may span multiple tasks when previous tasks finish
  /// and new ones are created. Stored oldest-first.
  @HiveField(7)
  List<String> taskIds;

  ChatSession({
    required this.id,
    this.taskId,
    this.contextId,
    this.analysisId,
    required this.title,
    required this.createdAt,
    required this.updatedAt,
    List<String>? taskIds,
  }) : taskIds = taskIds ?? [];

  /// Adds a task ID to the list if not already present.
  void addTaskId(String id) {
    if (!taskIds.contains(id)) {
      taskIds.add(id);
    }
  }
}
