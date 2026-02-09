import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:astro_guide/core/theme/app_theme.dart';
import 'package:intl/intl.dart';
import 'package:astro_guide/l10n/generated/app_localizations.dart';
import 'package:astro_guide/features/logbook/models/logbook_entry.dart';
import 'package:astro_guide/features/logbook/providers/logbook_provider.dart';

/// Logbook Screen - History gallery of discoveries.
///
/// Features:
/// - Dark image grid with actual saved analyses
/// - Search bar for filtering by object name
/// - FAB to navigate to Observatory for new capture
class LogbookScreen extends ConsumerStatefulWidget {
  const LogbookScreen({super.key});

  @override
  ConsumerState<LogbookScreen> createState() => _LogbookScreenState();
}

class _LogbookScreenState extends ConsumerState<LogbookScreen> {
  String _searchQuery = '';

  @override
  Widget build(BuildContext context) {
    final entries = ref.watch(logbookEntriesProvider);

    // Filter entries by search query
    final filteredEntries = _searchQuery.isEmpty
        ? entries
        : entries
              .where(
                (entry) => entry.title.toLowerCase().contains(
                  _searchQuery.toLowerCase(),
                ),
              )
              .toList();

    return Scaffold(
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 16),
              child: Text(
                AppLocalizations.of(context)!.logbookTitle,
                style: AppTextStyles.display(),
              ),
            ),
            // Search bar
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: _SearchBar(
                onChanged: (query) => setState(() => _searchQuery = query),
              ),
            ),
            const SizedBox(height: 20),
            // Grid of discoveries
            Expanded(
              child: filteredEntries.isEmpty
                  ? _buildEmptyState()
                  : _DiscoveriesGrid(entries: filteredEntries),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.go('/observatory'),
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.auto_awesome,
            size: 72,
            color: AppColors.cyanAccent.withOpacity(0.3),
          ),
          const SizedBox(height: 16),
          Text(
            _searchQuery.isEmpty
                ? AppLocalizations.of(context)!.logbookEmpty
                : AppLocalizations.of(context)!.logbookNoResults,
            style: AppTextStyles.headline(color: AppColors.textMuted),
          ),
          const SizedBox(height: 8),
          Text(
            _searchQuery.isEmpty
                ? AppLocalizations.of(context)!.logbookEmptyHint
                : AppLocalizations.of(context)!.logbookNoResultsHint,
            style: AppTextStyles.body(color: AppColors.textMuted),
          ),
          if (_searchQuery.isEmpty) ...[
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => context.go('/observatory'),
              icon: const Icon(Icons.camera_alt),
              label: Text(AppLocalizations.of(context)!.goToObservatory),
            ),
          ],
        ],
      ),
    );
  }
}

class _SearchBar extends StatelessWidget {
  final ValueChanged<String> onChanged;

  const _SearchBar({required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.surfaceElevated),
      ),
      child: Row(
        children: [
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Icon(Icons.search, color: AppColors.textMuted),
          ),
          Expanded(
            child: TextField(
              onChanged: onChanged,
              decoration: InputDecoration(
                hintText: AppLocalizations.of(context)!.logbookSearchHint,
                hintStyle: AppTextStyles.body(color: AppColors.textMuted),
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(vertical: 14),
              ),
              style: AppTextStyles.body(),
            ),
          ),
        ],
      ),
    );
  }
}

class _DiscoveriesGrid extends StatelessWidget {
  final List<LogbookEntry> entries;

  const _DiscoveriesGrid({required this.entries});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final crossAxisCount = constraints.maxWidth > 1200
            ? 4
            : constraints.maxWidth > 800
            ? 3
            : 2;

        return GridView.builder(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount,
            mainAxisSpacing: 20,
            crossAxisSpacing: 20,
            childAspectRatio: 0.85,
          ),
          itemCount: entries.length,
          itemBuilder: (context, index) {
            final entry = entries[index];
            return _DiscoveryCard(entry: entry);
          },
        );
      },
    );
  }
}

class _DiscoveryCard extends ConsumerWidget {
  final LogbookEntry entry;

  const _DiscoveryCard({required this.entry});

  String _formatDate(BuildContext context, DateTime date) {
    return DateFormat.yMMMd(
      AppLocalizations.of(context)!.localeName,
    ).format(date);
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(
          AppLocalizations.of(context)!.deleteLogTitle ?? 'Delete Log',
        ),
        content: Text(
          AppLocalizations.of(context)!.deleteLogMessage ??
              'Are you sure you want to delete this log? This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(AppLocalizations.of(context)!.cancelButton),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            child: Text(AppLocalizations.of(context)!.deleteButton),
          ),
        ],
      ),
    );

    if (confirm == true) {
      await ref.read(logbookEntriesProvider.notifier).removeEntry(entry.uid);
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return GestureDetector(
      onTap: () => context.go('/results/${entry.uid}'),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          color: AppColors.surface,
        ),
        clipBehavior: Clip.antiAlias,
        child: Stack(
          fit: StackFit.expand,
          children: [
            // Thumbnail image
            Image.memory(
              entry.thumbnailBytes,
              fit: BoxFit.cover,
              errorBuilder: (context, error, stackTrace) => Container(
                color: AppColors.surfaceElevated,
                child: const Center(
                  child: Icon(
                    Icons.auto_awesome,
                    size: 48,
                    color: AppColors.cyanAccent,
                  ),
                ),
              ),
            ),
            // Gradient overlay for text
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.transparent,
                      AppColors.background.withOpacity(0.9),
                    ],
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      entry.title,
                      style: AppTextStyles.label(fontWeight: FontWeight.w600),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(
                          Icons.calendar_today,
                          size: 12,
                          color: AppColors.cyanAccent,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          _formatDate(context, entry.timestamp),
                          style: AppTextStyles.caption(
                            color: AppColors.cyanAccent,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            // Trash Button
            Positioned(
              top: 8,
              right: 8,
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  onTap: () => _confirmDelete(context, ref),
                  borderRadius: BorderRadius.circular(20),
                  child: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.4),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.delete_outline,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
