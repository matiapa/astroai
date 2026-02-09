import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:astro_guide/core/theme/app_theme.dart';
import 'package:astro_guide/features/settings/providers/settings_provider.dart';
import 'package:astro_guide/l10n/generated/app_localizations.dart';

/// Settings Screen - App preferences and configuration.
///
/// Features:
/// - Auto-play narration toggle
/// - Language selection
/// - About section
class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            // Header
            Text(l10n.settingsTitle, style: AppTextStyles.display()),
            const SizedBox(height: 32),

            // Playback section
            _SectionHeader(title: l10n.settingsPlaybackSection),
            const SizedBox(height: 12),
            _SettingsTile(
              icon: Icons.play_circle_outline,
              title: l10n.settingsAutoPlay,
              subtitle: l10n.settingsAutoPlaySubtitle,
              trailing: Switch(
                value: settings.autoPlayNarration,
                onChanged: (value) {
                  ref.read(settingsProvider.notifier).toggleAutoPlay(value);
                },
                activeThumbColor: AppColors.cyanAccent,
              ),
            ),

            const SizedBox(height: 32),

            // Language section
            _SectionHeader(title: l10n.settingsLanguageSection),
            const SizedBox(height: 12),
            _SettingsTile(
              icon: Icons.language,
              title: l10n.settingsLanguage,
              trailing: DropdownButton<String>(
                // Use settings locale or active system locale
                value:
                    settings.locale ??
                    Localizations.localeOf(context).languageCode,
                dropdownColor: AppColors.surface,
                style: AppTextStyles.body(),
                underline: const SizedBox(),
                items: [
                  DropdownMenuItem(
                    value: 'en',
                    child: Text(l10n.settingsLanguageEn),
                  ),
                  DropdownMenuItem(
                    value: 'es',
                    child: Text(l10n.settingsLanguageEs),
                  ),
                ],
                onChanged: (String? newValue) {
                  if (newValue != null) {
                    ref.read(settingsProvider.notifier).setLocale(newValue);
                  }
                },
              ),
            ),

            const SizedBox(height: 32),

            // About section
            _SectionHeader(title: l10n.settingsAboutSection),
            const SizedBox(height: 12),
            _SettingsTile(
              icon: Icons.auto_awesome,
              title: 'AstroGuide',
              subtitle: l10n.settingsVersion('0.1.0'),
            ),
            const SizedBox(height: 8),
            _SettingsTile(
              icon: Icons.info_outline,
              title: l10n.settingsOpenSourceLicenses,
              onTap: () {
                showLicensePage(context: context);
              },
            ),
            const SizedBox(height: 8),
            _SettingsTile(
              icon: Icons.image_search_outlined,
              title: l10n.settingsCatalogSource,
              subtitle: l10n.settingsCatalogSourceSubtitle,
              onTap: () async {
                final url = Uri.parse(
                  'https://waps.cfa.harvard.edu/microobservatory/MOImageDirectory/ImageDirectory.php#Object_3633',
                );
                if (await canLaunchUrl(url)) {
                  await launchUrl(url);
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;

  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Text(
      title.toUpperCase(),
      style: AppTextStyles.technical(
        fontSize: 12,
        color: AppColors.cyanAccent,
        fontWeight: FontWeight.bold,
      ),
    );
  }
}

class _SettingsTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;

  const _SettingsTile({
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailing,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.surfaceElevated),
          ),
          child: Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: AppColors.cyanAccent.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: AppColors.cyanAccent, size: 20),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: AppTextStyles.label()),
                    if (subtitle != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        subtitle!,
                        style: AppTextStyles.caption(),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ],
                ),
              ),
              ?trailing,
              if (trailing == null && onTap != null)
                const Icon(Icons.chevron_right, color: AppColors.textMuted),
            ],
          ),
        ),
      ),
    );
  }
}
