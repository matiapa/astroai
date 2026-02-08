import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_ai_toolkit/flutter_ai_toolkit.dart';
import 'package:a2a/a2a.dart';
import 'package:uuid/uuid.dart';

/// Custom [LlmProvider] that bridges the Flutter AI Toolkit to the
/// A2A (Agent-to-Agent) protocol using direct Dio HTTP + SSE streaming.
///
/// This provider bypasses [A2AClient] entirely because:
/// - The `a2a` package's agent card parser crashes on minimal capabilities.
/// - Without the card, [A2AClient.sendMessageStream] refuses to run.
///
/// Instead, we POST JSON-RPC requests directly via Dio and parse the
/// Server-Sent Events stream ourselves. A2A data models are still used
/// for message serialization and response deserialization.
class A2aProvider extends LlmProvider with ChangeNotifier {
  /// The Dio HTTP client.
  final Dio _dio;

  /// The A2A agent endpoint URL.
  final String _agentUrl;

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

  /// UUID generator for message IDs and JSON-RPC request IDs.
  static const _uuid = Uuid();

  /// Creates an [A2aProvider] instance.
  ///
  /// - [agentUrl]: The A2A agent's base URL (JSON-RPC endpoint).
  /// - [initialContext]: Optional context string to prepend to the first
  ///   message (e.g., analysis summary for ResultsChat).
  /// - [history]: Optional initial chat history for session restoration.
  /// - [taskId]: Optional A2A task ID to resume an existing conversation.
  /// - [contextId]: Optional A2A context ID to resume an existing conversation.
  A2aProvider({
    required String agentUrl,
    String? initialContext,
    Iterable<ChatMessage>? history,
    String? taskId,
    String? contextId,
  })  : _agentUrl = agentUrl.replaceAll(RegExp(r'/$'), ''),
        _dio = Dio(),
        _initialContext = initialContext,
        _history = history?.toList() ?? [],
        _taskId = taskId,
        _contextId = contextId;

  /// The current A2A task ID, or null if no message has been sent yet.
  String? get taskId => _taskId;

  /// The current A2A context ID, or null if no message has been sent yet.
  String? get contextId => _contextId;

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

    final response =
        _callAgent(prompt, attachments: attachments, updateHistory: true);

    yield* response.map((chunk) {
      llmMessage.append(chunk);
      return chunk;
    });

    notifyListeners();
  }

  /// Core method that sends a message to the A2A agent via SSE streaming
  /// and yields text chunks as they arrive.
  Stream<String> _callAgent(
    String prompt, {
    required Iterable<Attachment> attachments,
    required bool updateHistory,
  }) async* {
    // Build message parts
    final parts = <A2APart>[];

    // If this is the first message and we have initial context, prepend it
    if (!_contextSent &&
        _initialContext != null &&
        _initialContext.isNotEmpty) {
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

    // Convert attachments to A2A file parts
    for (final attachment in attachments) {
      if (attachment is FileAttachment) {
        final fileWithBytes = A2AFileWithBytes()
          ..bytes = base64Encode(attachment.bytes)
          ..mimeType = attachment.mimeType
          ..name = attachment.name;
        final filePart = A2AFilePart()
          ..kind = 'file'
          ..file = fileWithBytes;
        parts.add(filePart);
      } else if (attachment is LinkAttachment) {
        final fileWithUri = A2AFileWithUri()
          ..uri = attachment.url.toString()
          ..mimeType = attachment.mimeType
          ..name = attachment.name;
        final filePart = A2AFilePart()
          ..kind = 'file'
          ..file = fileWithUri;
        parts.add(filePart);
      }
    }

    // Build the A2A message
    final message = A2AMessage()
      ..role = 'user'
      ..messageId = _uuid.v4()
      ..kind = 'message'
      ..parts = parts;

    // Set contextId if continuing a conversation (to group related tasks)
    // NOTE: We intentionally do NOT set taskId here. If the previous task
    // is finished, the server will create a new task in the same context.
    if (_contextId != null) {
      message.contextId = _contextId;
    }

    // Build send params and JSON-RPC 2.0 envelope
    final params = A2AMessageSendParams()..message = message;
    final rpcRequest = {
      'jsonrpc': '2.0',
      'method': 'message/stream',
      'params': params.toJson(),
      'id': _uuid.v4(),
    };

    try {
      final httpResponse = await _dio.post<ResponseBody>(
        _agentUrl,
        data: rpcRequest,
        options: Options(
          contentType: 'application/json',
          responseType: ResponseType.stream,
          headers: {'Accept': 'text/event-stream'},
        ),
      );

      final responseStream = httpResponse.data;
      if (responseStream == null) {
        throw Exception('A2A Error: empty response from agent');
      }

      // Parse the SSE stream, deduplicating accumulated chunks.
      //
      // The ADK server sends incremental text deltas AND a final
      // accumulated message containing the full response. Without
      // deduplication the text would appear doubled in the chat bubble.
      final accumulated = StringBuffer();

      await for (final chunk in _parseSseStream(responseStream.stream)) {
        final accText = accumulated.toString();

        if (accText.isNotEmpty && chunk.startsWith(accText)) {
          // The chunk is an accumulated response that supersedes the
          // deltas we've already yielded. Only emit the truly new tail.
          final newPart = chunk.substring(accText.length);
          if (newPart.isNotEmpty) {
            accumulated.write(newPart);
            yield newPart;
          }
        } else if (accText.isNotEmpty && accText.endsWith(chunk)) {
          // The chunk is a subset of what we already streamed — skip.
        } else {
          accumulated.write(chunk);
          yield chunk;
        }
      }
    } on DioException catch (e) {
      debugPrint('A2aProvider DioException: ${e.message}');
      throw Exception('A2A network error: ${e.message}');
    } catch (e) {
      debugPrint('A2aProvider error: $e');
      rethrow;
    }
  }

  /// Parses a Server-Sent Events byte stream into text chunks.
  ///
  /// Each SSE event is one or more lines. Lines starting with `data:` carry
  /// JSON-RPC payloads. Each `data:` line is treated as a separate JSON object.
  Stream<String> _parseSseStream(Stream<Uint8List> byteStream) async* {
    final lineBuffer = StringBuffer();

    await for (final chunk in byteStream
        .cast<List<int>>()
        .transform(utf8.decoder)) {
      lineBuffer.write(chunk);

      // Split on any newline variant and process complete lines
      var content = lineBuffer.toString();
      // Normalize \r\n to \n, then lone \r to \n
      content = content.replaceAll('\r\n', '\n').replaceAll('\r', '\n');

      // Process all complete lines (ending with \n)
      final lastNewline = content.lastIndexOf('\n');
      if (lastNewline == -1) continue; // No complete line yet

      final completeLines = content.substring(0, lastNewline);
      final remainder = content.substring(lastNewline + 1);

      lineBuffer.clear();
      lineBuffer.write(remainder);

      for (final line in completeLines.split('\n')) {
        final trimmed = line.trim();
        if (trimmed.startsWith('data:')) {
          final jsonStr = trimmed.substring(5).trim();
          if (jsonStr.isNotEmpty) {
            final text = _processJsonPayload(jsonStr);
            if (text != null && text.isNotEmpty) {
              yield text;
            }
          }
        }
        // Ignore event:, id:, retry:, comments (:), and blank lines
      }
    }

    // Process any remaining data in the buffer
    final remaining = lineBuffer.toString().trim();
    if (remaining.startsWith('data:')) {
      final jsonStr = remaining.substring(5).trim();
      if (jsonStr.isNotEmpty) {
        final text = _processJsonPayload(jsonStr);
        if (text != null && text.isNotEmpty) {
          yield text;
        }
      }
    }
  }

  /// Parses a single JSON-RPC payload from an SSE `data:` line.
  String? _processJsonPayload(String jsonStr) {
    try {
      final json = jsonDecode(jsonStr) as Map<String, dynamic>;

      // Check for JSON-RPC error
      if (json.containsKey('error')) {
        final error = json['error'];
        final errorMsg = error is Map
            ? (error['message'] ?? 'Unknown error')
            : 'Unknown error';
        debugPrint('A2aProvider SSE error: $errorMsg');
        return null;
      }

      // Parse the result
      final resultJson = json['result'];
      if (resultJson != null && resultJson is Map<String, dynamic>) {
        final result = _parseResult(resultJson);
        if (result != null) {
          return _extractTextFromResult(result);
        }
      }
    } catch (e) {
      debugPrint('A2aProvider: failed to parse JSON payload: $e');
    }

    return null;
  }

  /// Parses the JSON-RPC result into the appropriate A2A model.
  dynamic _parseResult(Map<String, dynamic> json) {
    // A2ATaskStatusUpdateEvent has 'kind' == 'status-update'
    if (json['kind'] == 'status-update') {
      return A2ATaskStatusUpdateEvent.fromJson(json);
    }
    // A2ATask has 'id' and 'status' fields
    if (json.containsKey('status') && json.containsKey('id')) {
      return A2ATask.fromJson(json);
    }
    // A2AMessage has 'role' and 'parts' fields
    if (json.containsKey('role') && json.containsKey('parts')) {
      return A2AMessage.fromJson(json);
    }
    debugPrint('A2aProvider: unknown result type: ${json.keys}');
    return null;
  }

  /// Extracts text content from an A2A result object.
  ///
  /// The result can be one of:
  /// - [A2ATaskStatusUpdateEvent]: Contains status with message parts
  /// - [A2ATask]: Contains status with message parts, plus artifacts
  /// - [A2AMessage]: Direct message with parts
  ///
  /// Only extracts text from **agent** messages; user-role messages echoed
  /// back by the server are skipped to avoid mixing user input into the
  /// LLM response stream.
  String? _extractTextFromResult(dynamic result) {
    if (result is A2ATaskStatusUpdateEvent) {
      _taskId = result.taskId;
      _contextId = result.contextId;
      return _extractAgentTextFromMessage(result.status?.message);
    } else if (result is A2ATask) {
      _taskId = result.id;
      _contextId = result.contextId;

      final statusText =
          _extractAgentTextFromMessage(result.status?.message);

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
      return _extractAgentTextFromMessage(result);
    }

    return null;
  }

  /// Extracts text from an [A2AMessage]'s parts, but only if the message
  /// has role `"agent"`. Returns `null` for user-role messages so that
  /// echoed user text is never yielded as an LLM response chunk.
  String? _extractAgentTextFromMessage(A2AMessage? message) {
    if (message == null || message.parts == null) return null;
    // Skip user-role messages echoed back by the server
    if (message.role == 'user') return null;

    final textParts = message.parts!
        .whereType<A2ATextPart>()
        .map((part) => part.text)
        .where((text) => text.isNotEmpty)
        .toList();

    return textParts.isNotEmpty ? textParts.join('\n') : null;
  }

  /// Extracts text from an [A2AMessage]'s parts regardless of role.
  /// Used by [fetchTaskHistory] where we need both user and agent text.
  String? _extractTextFromMessage(A2AMessage? message) {
    if (message == null || message.parts == null) return null;

    final textParts = message.parts!
        .whereType<A2ATextPart>()
        .map((part) => part.text)
        .where((text) => text.isNotEmpty)
        .toList();

    return textParts.isNotEmpty ? textParts.join('\n') : null;
  }

  // ---------------------------------------------------------------------------
  // History restoration via A2A tasks/get
  // ---------------------------------------------------------------------------

  /// Fetches the full conversation history from the A2A server by calling
  /// `tasks/get` for each task ID in [taskIds] and merging their message
  /// histories in order.
  ///
  /// A single conversation may span multiple A2A tasks (each task finishes,
  /// and the next user message creates a new task within the same context).
  /// This method reconstructs the full visual history across all of them.
  ///
  /// Returns `true` if at least one task was successfully fetched.
  Future<bool> fetchMultiTaskHistory(List<String> taskIds) async {
    if (taskIds.isEmpty) return false;

    _history.clear();
    String? lastRole;
    String? lastUserText;
    String? lastAgentText;
    ChatMessage? lastMsg;
    var anySuccess = false;

    // Fetch each task in order (oldest first — taskIds are stored oldest-first)
    for (final id in taskIds) {
      final task = await _fetchSingleTask(id);
      if (task == null) continue;
      anySuccess = true;

      // Keep the latest contextId for future messages
      if (task.contextId.isNotEmpty) {
        _contextId = task.contextId;
      }

      if (task.history == null) continue;

      for (final a2aMsg in task.history!) {
        final text = _extractTextFromMessage(a2aMsg) ?? '';
        if (text.isEmpty) continue;

        if (a2aMsg.role == 'user') {
          if (lastRole == 'user') {
            // Skip duplicate consecutive user messages (server echo)
            if (text == lastUserText) continue;
            // Genuinely different consecutive user text — append
            if (lastMsg != null) lastMsg.append('\n$text');
          } else {
            lastMsg = ChatMessage.user(text, const []);
            _history.add(lastMsg);
          }
          lastRole = 'user';
          lastUserText = text;
          lastAgentText = null;
        } else {
          // Agent message
          if (lastRole == 'agent' && lastMsg != null) {
            // Skip exact duplicate agent text (server often stores the
            // same response in both a status-update event and the final
            // agent message, leading to doubled text).
            if (text == lastAgentText) continue;
            // If the new text already contains what we have, replace
            // (accumulated response supersedes earlier partial).
            // If what we have already contains the new text, skip it.
            final existing = lastMsg.text ?? '';
            if (text.contains(existing)) {
              // New text is a superset — replace the bubble content.
              // ChatMessage doesn't support replace, so recreate.
              _history.removeLast();
              lastMsg = ChatMessage.llm();
              lastMsg.append(text);
              _history.add(lastMsg);
            } else if (!existing.contains(text)) {
              // Genuinely new content — append to the bubble.
              lastMsg.append(text);
            }
            // else: existing already contains this text — skip
          } else {
            lastMsg = ChatMessage.llm();
            lastMsg.append(text);
            _history.add(lastMsg);
            lastRole = 'agent';
            lastUserText = null;
          }
          lastAgentText = text;
        }
      }
    }

    if (anySuccess) {
      // Mark context as already sent (it was part of the original conversation)
      _contextSent = true;
      notifyListeners();
    }

    return anySuccess;
  }

  /// Fetches a single task from the A2A server via `tasks/get`.
  /// Returns `null` if the fetch fails for any reason.
  Future<A2ATask?> _fetchSingleTask(String taskId) async {
    final params = A2ATaskQueryParams()..id = taskId;

    final rpcRequest = {
      'jsonrpc': '2.0',
      'method': 'tasks/get',
      'params': params.toJson(),
      'id': _uuid.v4(),
    };

    try {
      final httpResponse = await _dio.post<Map<String, dynamic>>(
        _agentUrl,
        data: rpcRequest,
        options: Options(contentType: 'application/json'),
      );

      final json = httpResponse.data;
      if (json == null) {
        debugPrint('A2aProvider._fetchSingleTask: empty response for $taskId');
        return null;
      }

      if (json.containsKey('error')) {
        final error = json['error'];
        final errorMsg =
            error is Map ? (error['message'] ?? 'Unknown error') : 'Unknown';
        debugPrint('A2aProvider._fetchSingleTask error for $taskId: $errorMsg');
        return null;
      }

      final resultJson = json['result'] as Map<String, dynamic>?;
      if (resultJson == null) return null;

      return A2ATask.fromJson(resultJson);
    } catch (e) {
      debugPrint('A2aProvider._fetchSingleTask error for $taskId: $e');
      return null;
    }
  }
}
