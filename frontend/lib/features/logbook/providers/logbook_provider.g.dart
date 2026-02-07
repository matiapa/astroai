// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'logbook_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$logbookServiceHash() => r'88528f619d3dbb192d01b6a2bb75d683e0695bf4';

/// Provider for the [LogbookService].
///
/// Copied from [logbookService].
@ProviderFor(logbookService)
final logbookServiceProvider = AutoDisposeProvider<LogbookService>.internal(
  logbookService,
  name: r'logbookServiceProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$logbookServiceHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef LogbookServiceRef = AutoDisposeProviderRef<LogbookService>;
String _$logbookEntriesHash() => r'd5b0956042ea92d97409f9ab6e4d8cc5a9b0f7a7';

/// Provider for the list of logbook entries.
///
/// Watches for changes and rebuilds when entries are added/removed.
///
/// Copied from [LogbookEntries].
@ProviderFor(LogbookEntries)
final logbookEntriesProvider =
    AutoDisposeNotifierProvider<LogbookEntries, List<LogbookEntry>>.internal(
      LogbookEntries.new,
      name: r'logbookEntriesProvider',
      debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
          ? null
          : _$logbookEntriesHash,
      dependencies: null,
      allTransitiveDependencies: null,
    );

typedef _$LogbookEntries = AutoDisposeNotifier<List<LogbookEntry>>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
