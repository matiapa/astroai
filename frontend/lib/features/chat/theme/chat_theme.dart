import 'package:flutter/material.dart';
import 'package:flutter_ai_toolkit/flutter_ai_toolkit.dart';
import 'package:flutter_markdown_plus/flutter_markdown_plus.dart';
import 'package:google_fonts/google_fonts.dart';

import 'package:astro_guide/core/theme/app_theme.dart';

/// Provides a custom [LlmChatViewStyle] that matches the AstroGuide
/// "Deep Space" theme (OLED black background, cyan accents).
class ChatTheme {
  ChatTheme._();

  /// Base text style for LLM markdown content — white on dark bubble.
  static TextStyle get _llmBaseText => GoogleFonts.inter(
        color: AppColors.textPrimary,
        fontSize: 15,
        height: 1.5,
      );

  /// Markdown style sheet for LLM messages with high-contrast white text.
  static MarkdownStyleSheet _llmMarkdownStyle() => MarkdownStyleSheet(
        p: _llmBaseText,
        a: _llmBaseText.copyWith(
          color: AppColors.cyanAccent,
          decoration: TextDecoration.underline,
        ),
        strong: _llmBaseText.copyWith(fontWeight: FontWeight.bold),
        em: _llmBaseText.copyWith(fontStyle: FontStyle.italic),
        del: _llmBaseText.copyWith(decoration: TextDecoration.lineThrough),
        h1: _llmBaseText.copyWith(fontSize: 22, fontWeight: FontWeight.bold),
        h2: _llmBaseText.copyWith(fontSize: 19, fontWeight: FontWeight.bold),
        h3: _llmBaseText.copyWith(fontSize: 17, fontWeight: FontWeight.bold),
        h4: _llmBaseText.copyWith(fontWeight: FontWeight.bold),
        h5: _llmBaseText,
        h6: _llmBaseText,
        listBullet: _llmBaseText,
        blockquote: _llmBaseText.copyWith(
          color: AppColors.textSecondary,
          fontStyle: FontStyle.italic,
        ),
        code: GoogleFonts.jetBrainsMono(
          color: AppColors.cyanAccent,
          fontSize: 13,
          backgroundColor: const Color(0xFF1A1A2E),
        ),
        tableBody: _llmBaseText,
        tableHead: _llmBaseText.copyWith(fontWeight: FontWeight.bold),
        img: _llmBaseText,
        checkbox: _llmBaseText,
      );

  /// The Deep Space styled [LlmChatViewStyle] for use with [LlmChatView].
  static LlmChatViewStyle get deepSpaceStyle => LlmChatViewStyle(
        backgroundColor: AppColors.background,
        menuColor: AppColors.surfaceElevated,
        progressIndicatorColor: AppColors.cyanAccent,
        userMessageStyle: UserMessageStyle(
          textStyle: GoogleFonts.inter(
            color: AppColors.textPrimary,
            fontSize: 15,
            height: 1.4,
          ),
          decoration: BoxDecoration(
            color: AppColors.cyanAccent.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: AppColors.cyanAccent.withValues(alpha: 0.25),
            ),
          ),
        ),
        llmMessageStyle: LlmMessageStyle(
          icon: Icons.auto_awesome,
          iconColor: AppColors.cyanAccent,
          iconDecoration: BoxDecoration(
            color: AppColors.cyanAccent.withValues(alpha: 0.12),
            shape: BoxShape.circle,
          ),
          markdownStyle: _llmMarkdownStyle(),
          decoration: BoxDecoration(
            color: const Color(0xFF2D2D44),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: const Color(0xFF3E3E5C),
            ),
          ),
        ),
        chatInputStyle: ChatInputStyle(
          textStyle: GoogleFonts.inter(
            color: AppColors.textPrimary,
            fontSize: 15,
          ),
          hintStyle: GoogleFonts.inter(
            color: AppColors.textMuted,
            fontSize: 15,
          ),
          backgroundColor: AppColors.surface,
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: AppColors.surfaceElevated,
            ),
          ),
        ),
        submitButtonStyle: const ActionButtonStyle(
          iconColor: AppColors.cyanAccent,
          iconDecoration: BoxDecoration(
            color: Colors.transparent,
            shape: BoxShape.circle,
          ),
        ),
        addButtonStyle: ActionButtonStyle(
          iconColor: AppColors.textSecondary,
          iconDecoration: BoxDecoration(
            color: AppColors.surfaceElevated,
            shape: BoxShape.circle,
            border: Border.all(
              color: AppColors.textMuted.withValues(alpha: 0.3),
            ),
          ),
        ),
        recordButtonStyle: const ActionButtonStyle(
          iconColor: AppColors.cyanAccent,
        ),
        stopButtonStyle: const ActionButtonStyle(
          iconColor: AppColors.error,
        ),
        copyButtonStyle: const ActionButtonStyle(
          iconColor: AppColors.textMuted,
        ),
        editButtonStyle: const ActionButtonStyle(
          iconColor: AppColors.textMuted,
        ),
        closeButtonStyle: const ActionButtonStyle(
          iconColor: AppColors.textMuted,
        ),
        cancelButtonStyle: const ActionButtonStyle(
          iconColor: AppColors.textMuted,
        ),
        suggestionStyle: SuggestionStyle(
          textStyle: GoogleFonts.inter(
            color: AppColors.cyanAccent,
            fontSize: 14,
          ),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: AppColors.cyanAccent.withValues(alpha: 0.3),
            ),
          ),
        ),
        actionButtonBarDecoration: BoxDecoration(
          color: AppColors.background,
          border: Border(
            top: BorderSide(
              color: AppColors.surfaceElevated,
              width: 1,
            ),
          ),
        ),
        attachFileButtonStyle: ActionButtonStyle(
          iconColor: AppColors.textSecondary,
          textStyle: GoogleFonts.inter(
            color: AppColors.textPrimary, // High contrast white
            fontSize: 15,
            fontWeight: FontWeight.w500,
          ),
        ),
        cameraButtonStyle: ActionButtonStyle(
          iconColor: AppColors.textSecondary,
          textStyle: GoogleFonts.inter(
            color: AppColors.textPrimary, // High contrast white
            fontSize: 15,
            fontWeight: FontWeight.w500,
          ),
        ),
        galleryButtonStyle: ActionButtonStyle(
          iconColor: AppColors.textSecondary,
          textStyle: GoogleFonts.inter(
            color: AppColors.textPrimary, // High contrast white
            fontSize: 15,
            fontWeight: FontWeight.w500,
          ),
        ),
      );
}
