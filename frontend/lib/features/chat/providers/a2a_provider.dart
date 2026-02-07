import 'package:flutter/foundation.dart';
import 'package:flutter_ai_toolkit/flutter_ai_toolkit.dart';
import 'package:a2a/a2a.dart';
import 'package:uuid/uuid.dart';

/// Custom [LlmProvider] that bridges the Flutter AI Toolkit to the
/// A2A (Agent-to-Agent) protocol via [A2AClient].
///
/// This provider translates between the [LlmChatView] widget's expectations
/// and the A2A protocol's streaming message API, enabling multi-turn
/// conversations with a remote A2A agent (Atlas).
class A2aProvider extends LlmProvider with ChangeNotifier {
  /// The A2A client used to communicate with the remote agent.
  final A2AClient _client;

  /// Optional context string prepended to the first user message.
  /// Used by ResultsChat to inject analysis context.
  final String? _initialContext;

  /// Internal chat history for the AI Toolkit.
  final List<ChatMessage> _history;

  /// A2A task ID for the current conversation. Assigned by the server
  /// after the first message and reused for multi-turn.
  String? _taskId;

  /// A2A context ID for grouping related tasks. Assigned by the server.
  String? _contextId;

  /// Tracks whether the initial context has already been sent.
  bool _contextSent = false;

  /// UUID generator for message IDs.
  static const _uuid = Uuid();

  /// Creates an [A2aProvider] instance.
  ///
  /// - [client]: An initialized [A2AClient] pointing to the A2A agent.
  /// - [initialContext]: Optional context string to prepend to the first
  ///   message (e.g., analysis summary for ResultsChat).
  /// - [history]: Optional initial chat history for session restoration.
  A2aProvider({
    required A2AClient client,
    String? initialContext,
    Iterable<ChatMessage>? history,
  })  : _client = client,
        _initialContext = initialContext,
        _history = history?.toList() ?? [];

  @override
  Iterable<ChatMessage> get history => _history;

  @override
  set history(Iterable<ChatMessage> history) {
    _history.clear();
    _history.addAll(history);
    // Reset A2A state when history is replaced (new conversation)
    _taskId = null;
    _contextId = null;
    _contextSent = false;
    notifyListeners();
  }

  @override
  Stream<String> generateStream(
    String prompt, {
    Iterable<Attachment> attachments = const [],
  }) async* {
    yield* _callAgent(prompt, attachments: attachments, updateHistory: false);
  }

  @override
  Stream<String> sendMessageStream(
    String prompt, {
    Iterable<Attachment> attachments = const [],
  }) async* {
    final userMessage = ChatMessage.user(prompt, attachments);
    final llmMessage = ChatMessage.llm();
    _history.addAll([userMessage, llmMessage]);

    final response = _callAgent(prompt, attachments: attachments, updateHistory: true);

    yield* response.map((chunk) {
      llmMessage.append(chunk);
      return chunk;
    });

    notifyListeners();
  }

  /// Core method that sends a message to the A2A agent and yields text chunks.
  Stream<String> _callAgent(
    String prompt, {
    required Iterable<Attachment> attachments,
    required bool updateHistory,
  }) async* {
    // Build message parts
    final parts = <A2APart>[];

    // If this is the first message and we have initial context, prepend it
    if (!_contextSent && _initialContext != null && _initialContext.isNotEmpty) {
      final contextPart = A2ATextPart()
        ..kind = 'text'
        ..text = _initialContext;
      parts.add(contextPart);
      _contextSent = true;
    }

    // Add the user's text prompt
    final textPart = A2ATextPart()
      ..kind = 'text'
      ..text = prompt;
    parts.add(textPart);

    // Build the A2A message
    final message = A2AMessage()
      ..role = 'user'
      ..messageId = _uuid.v4()
      ..kind = 'message'
      ..parts = parts;

    // Set taskId and contextId if continuing a conversation
    if (_taskId != null) {
      message.taskId = _taskId;
    }
    if (_contextId != null) {
      message.contextId = _contextId;
    }

    // Build send params
    final params = A2AMessageSendParams()..message = message;

    try {
      final stream = _client.sendMessageStream(params);

      await for (final response in stream) {
        if (response.isError) {
          final errorResponse = response as A2AJSONRPCErrorResponseSSM;
          final errorCode = errorResponse.error?.rpcErrorCode;
          final errorMsg = errorCode != null
              ? A2AError.asString(errorCode)
              : 'Unknown error';
          throw Exception('A2A Error: $errorMsg');
        }

        final successResponse = response as A2ASendStreamMessageSuccessResponse;
        final result = successResponse.result;

        if (result == null) continue;

        // Handle different result types
        final text = _extractTextFromResult(result);
        if (text != null && text.isNotEmpty) {
          yield text;
        }
      }
    } catch (e) {
      debugPrint('A2aProvider error: $e');
      rethrow;
    }
  }

  /// Extracts text content from an A2A result object.
  ///
  /// The result can be one of:
  /// - [A2ATaskStatusUpdateEvent]: Contains status with message parts
  /// - [A2ATask]: Contains status with message parts, plus artifacts
  /// - [A2AMessage]: Direct message with parts
  String? _extractTextFromResult(dynamic result) {
    if (result is A2ATaskStatusUpdateEvent) {
      // Track task/context IDs
      _taskId = result.taskId;
      _contextId = result.contextId;

      return _extractTextFromMessage(result.status?.message);
    } else if (result is A2ATask) {
      // Track task/context IDs
      _taskId = result.id;
      _contextId = result.contextId;

      // First try the status message
      final statusText = _extractTextFromMessage(result.status?.message);

      // Then try artifacts
      final artifactTexts = <String>[];
      if (result.artifacts != null) {
        for (final artifact in result.artifacts!) {
          for (final part in artifact.parts) {
            if (part is A2ATextPart) {
              artifactTexts.add(part.text);
            }
          }
        }
      }

      final allTexts = [
        if (statusText != null && statusText.isNotEmpty) statusText,
        ...artifactTexts,
      ];

      return allTexts.isNotEmpty ? allTexts.join('\n') : null;
    } else if (result is A2AMessage) {
      return _extractTextFromMessage(result);
    }

    return null;
  }

  /// Extracts text from an [A2AMessage]'s parts.
  String? _extractTextFromMessage(A2AMessage? message) {
    if (message == null || message.parts == null) return null;

    final textParts = message.parts!
        .whereType<A2ATextPart>()
        .map((part) => part.text)
        .where((text) => text.isNotEmpty)
        .toList();

    return textParts.isNotEmpty ? textParts.join('\n') : null;
  }
}
