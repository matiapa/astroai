import 'package:flutter/material.dart';
import 'package:flutter_ai_toolkit/flutter_ai_toolkit.dart';
import 'package:uuid/uuid.dart';

import 'package:astro_guide/core/config/app_config.dart';
import 'package:astro_guide/core/theme/app_theme.dart';
import 'package:astro_guide/features/chat/models/chat_session.dart';
import 'package:astro_guide/features/chat/providers/a2a_provider.dart';
import 'package:astro_guide/features/chat/providers/chat_session_provider.dart';
import 'package:astro_guide/features/chat/theme/chat_theme.dart';
import 'package:astro_guide/l10n/generated/app_localizations.dart';

/// Main Chat Screen -- accessible as the 4th tab in the navigation bar.
///
/// Provides a general-purpose conversational interface with the Atlas AI
/// agent. Conversations are persisted via [ChatSession] and restored
/// from the A2A server using `tasks/get` when the screen is reopened.
class MainChatScreen extends StatefulWidget {
  const MainChatScreen({super.key});

  @override
  State<MainChatScreen> createState() => _MainChatScreenState();
}

class _MainChatScreenState extends State<MainChatScreen> {
  static const _uuid = Uuid();

  A2aProvider? _provider;
  ChatSession? _session;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _initSession();
  }

  /// Tries to restore the latest main-chat session from storage.
  /// Falls back to creating a fresh session if none exists or restoration
  /// fails.
  Future<void> _initSession() async {
    final saved = chatSessionServiceInstance.getLatestMainChatSession();

    if (saved != null && saved.taskIds.isNotEmpty) {
      // Attempt to restore from the server using all accumulated task IDs
      final provider = A2aProvider(
        agentUrl: AppConfig.a2aAgentUrl,
        contextId: saved.contextId,
      );

      final restored = await provider.fetchMultiTaskHistory(saved.taskIds);
      if (restored && mounted) {
        provider.addListener(() => _persistSession());
        setState(() {
          _provider = provider;
          _session = saved;
          _isLoading = false;
        });
        return;
      }
    }

    // No saved session or restoration failed -- start fresh
    _startFreshSession();
  }

  /// Creates a brand-new session and provider.
  void _startFreshSession() {
    final provider = A2aProvider(agentUrl: AppConfig.a2aAgentUrl);
    final session = ChatSession(
      id: _uuid.v4(),
      title: 'Atlas',
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );

    provider.addListener(() => _persistSession());

    if (mounted) {
      setState(() {
        _provider = provider;
        _session = session;
        _isLoading = false;
      });
    }
  }

  /// Saves the current session state to Hive whenever the provider
  /// notifies (i.e. after a message round-trip completes).
  void _persistSession() {
    final session = _session;
    final provider = _provider;
    if (session == null || provider == null) return;

    session.taskId = provider.taskId;
    session.contextId = provider.contextId;
    session.updatedAt = DateTime.now();

    // Accumulate the task ID so the full history can be reconstructed
    if (provider.taskId != null) {
      session.addTaskId(provider.taskId!);
    }

    // Use the first user message as the session title (once).
    if (session.title == 'Atlas' && provider.history.isNotEmpty) {
      final firstUserMsg = provider.history
          .where((m) => m.origin.isUser)
          .firstOrNull;
      if (firstUserMsg != null && firstUserMsg.text != null) {
        session.title = firstUserMsg.text!.length > 60
            ? '${firstUserMsg.text!.substring(0, 60)}...'
            : firstUserMsg.text!;
      }
    }

    chatSessionServiceInstance.saveSession(session);
  }

  /// Switches to a previously saved session, restoring its history from
  /// the server.
  Future<void> _switchToSession(ChatSession target) async {
    setState(() => _isLoading = true);

    if (target.taskIds.isNotEmpty) {
      final provider = A2aProvider(
        agentUrl: AppConfig.a2aAgentUrl,
        contextId: target.contextId,
      );

      final restored = await provider.fetchMultiTaskHistory(target.taskIds);
      if (restored && mounted) {
        provider.addListener(() => _persistSession());
        setState(() {
          _provider = provider;
          _session = target;
          _isLoading = false;
        });
        return;
      }
    }

    // Couldn't restore -- start fresh instead
    _startFreshSession();
  }

  /// Opens a bottom sheet listing past main-chat sessions.
  void _showHistory(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final sessions = chatSessionServiceInstance.getMainChatSessions();

    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Handle bar
              Container(
                margin: const EdgeInsets.only(top: 12, bottom: 8),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: AppColors.textMuted,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                child: Text(
                  l10n.chatHistory,
                  style: AppTextStyles.headline(fontSize: 16),
                ),
              ),
              if (sessions.isEmpty)
                Padding(
                  padding: const EdgeInsets.all(32),
                  child: Text(
                    l10n.chatNoHistory,
                    style:
                        AppTextStyles.body(color: AppColors.textMuted),
                  ),
                )
              else
                ConstrainedBox(
                  constraints: BoxConstraints(
                    maxHeight: MediaQuery.of(ctx).size.height * 0.4,
                  ),
                  child: ListView.builder(
                    shrinkWrap: true,
                    itemCount: sessions.length,
                    itemBuilder: (_, i) {
                      final s = sessions[i];
                      final isActive = s.id == _session?.id;
                      return ListTile(
                        leading: Icon(
                          isActive
                              ? Icons.chat_bubble
                              : Icons.chat_bubble_outline,
                          color: isActive
                              ? AppColors.cyanAccent
                              : AppColors.textSecondary,
                          size: 20,
                        ),
                        title: Text(
                          s.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: AppTextStyles.body(
                            color: isActive
                                ? AppColors.cyanAccent
                                : AppColors.textPrimary,
                          ),
                        ),
                        subtitle: Text(
                          _formatDate(s.updatedAt),
                          style: AppTextStyles.technical(
                            fontSize: 11,
                            color: AppColors.textMuted,
                          ),
                        ),
                        onTap: () {
                          Navigator.of(ctx).pop();
                          if (!isActive) {
                            _switchToSession(s);
                          }
                        },
                      );
                    },
                  ),
                ),
              const SizedBox(height: 8),
            ],
          ),
        );
      },
    );
  }

  String _formatDate(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inHours < 1) return '${diff.inMinutes}m ago';
    if (diff.inDays < 1) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return '${dt.day}/${dt.month}/${dt.year}';
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.cyanAccent.withValues(alpha: 0.12),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.auto_awesome,
                color: AppColors.cyanAccent,
                size: 18,
              ),
            ),
            const SizedBox(width: 10),
            Text(
              l10n.chatAtlasTitle,
              style: AppTextStyles.headline(fontSize: 18),
            ),
          ],
        ),
        centerTitle: true,
        actions: [
          // Conversation history
          IconButton(
            icon: const Icon(Icons.history, color: AppColors.textSecondary),
            tooltip: l10n.chatHistory,
            onPressed: () => _showHistory(context),
          ),
          // New conversation
          IconButton(
            icon: const Icon(Icons.add_comment_outlined,
                color: AppColors.textSecondary),
            tooltip: l10n.chatNewConversation,
            onPressed: () {
              setState(() => _isLoading = true);
              _startFreshSession();
            },
          ),
        ],
      ),
      body: _isLoading
          ? Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const CircularProgressIndicator(
                      color: AppColors.cyanAccent),
                  const SizedBox(height: 16),
                  Text(
                    l10n.chatLoadingHistory,
                    style:
                        AppTextStyles.body(color: AppColors.textSecondary),
                  ),
                ],
              ),
            )
          : LlmChatView(
              provider: _provider!,
              style: ChatTheme.deepSpaceStyle,
              welcomeMessage: l10n.chatWelcomeMessage,
              suggestions: [
                l10n.chatSuggestion1,
                l10n.chatSuggestion2,
                l10n.chatSuggestion3,
              ],
            ),
    );
  }
}
