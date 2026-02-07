// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'analysis_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$analysisServiceHash() => r'3f10b61671cdb91b786e1ff0ce77e565e959e796';

/// Provider for the [AnalysisService].
///
/// Copied from [analysisService].
@ProviderFor(analysisService)
final analysisServiceProvider = AutoDisposeProvider<AnalysisService>.internal(
  analysisService,
  name: r'analysisServiceProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$analysisServiceHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AnalysisServiceRef = AutoDisposeProviderRef<AnalysisService>;
String _$analysisControllerHash() =>
    r'acfe321892335e342d0e54a862445aa112bf2769';

/// Provider managing the state of the current analysis.
///
/// Copied from [AnalysisController].
@ProviderFor(AnalysisController)
final analysisControllerProvider =
    AutoDisposeNotifierProvider<
      AnalysisController,
      AsyncValue<AnalysisState>
    >.internal(
      AnalysisController.new,
      name: r'analysisControllerProvider',
      debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
          ? null
          : _$analysisControllerHash,
      dependencies: null,
      allTransitiveDependencies: null,
    );

typedef _$AnalysisController = AutoDisposeNotifier<AsyncValue<AnalysisState>>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
