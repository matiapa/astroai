import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'package:astro_guide/features/logbook/models/logbook_entry.dart';
import 'package:astro_guide/features/logbook/services/logbook_service.dart';

part 'logbook_provider.g.dart';

/// Global instance of the logbook service.
///
/// Initialized in main.dart before runApp().
final logbookServiceInstance = LogbookService();

/// Provider for the [LogbookService].
@riverpod
LogbookService logbookService(Ref ref) {
  return logbookServiceInstance;
}

/// Provider for the list of logbook entries.
///
/// Watches for changes and rebuilds when entries are added/removed.
@riverpod
class LogbookEntries extends _$LogbookEntries {
  @override
  List<LogbookEntry> build() {
    final service = ref.watch(logbookServiceProvider);
    return service.getAllEntries();
  }

  /// Adds a new entry to the logbook.
  Future<void> addEntry(LogbookEntry entry) async {
    final service = ref.read(logbookServiceProvider);
    await service.saveEntry(entry);
    state = service.getAllEntries();
  }

  /// Removes an entry from the logbook.
  Future<void> removeEntry(String uid) async {
    final service = ref.read(logbookServiceProvider);
    await service.deleteEntry(uid);
    state = service.getAllEntries();
  }

  /// Refreshes the entries list from storage.
  void refresh() {
    final service = ref.read(logbookServiceProvider);
    state = service.getAllEntries();
  }
}
