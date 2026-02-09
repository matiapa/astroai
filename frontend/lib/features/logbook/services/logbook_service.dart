import 'package:hive_ce_flutter/hive_flutter.dart';

import 'package:astro_guide/features/logbook/models/logbook_entry.dart';

/// Service for persisting and retrieving logbook entries using Hive.
class LogbookService {
  static const String _boxName = 'logbook';
  Box<LogbookEntry>? _box;

  /// Initializes the Hive box for logbook storage.
  ///
  /// Call this once during app startup after Hive.initFlutter().
  Future<void> initialize() async {
    if (!Hive.isAdapterRegistered(0)) {
      Hive.registerAdapter(LogbookEntryAdapter());
    }
    _box = await Hive.openBox<LogbookEntry>(_boxName);
  }

  /// Ensures the box is initialized.
  Box<LogbookEntry> get box {
    if (_box == null) {
      throw StateError(
        'LogbookService not initialized. Call initialize() first.',
      );
    }
    return _box!;
  }

  /// Saves a new logbook entry.
  Future<void> saveEntry(LogbookEntry entry) async {
    await box.put(entry.uid, entry);
  }

  /// Retrieves all entries sorted by timestamp (newest first).
  List<LogbookEntry> getAllEntries() {
    final entries = box.values.toList();
    entries.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    return entries;
  }

  /// Retrieves a single entry by UID.
  LogbookEntry? getEntry(String uid) {
    return box.get(uid);
  }

  /// Deletes an entry by UID.
  Future<void> deleteEntry(String uid) async {
    await box.delete(uid);
  }

  /// Returns the number of stored entries.
  int get entryCount => box.length;
}
