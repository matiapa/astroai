import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

import 'package:astro_guide/core/theme/app_theme.dart';
import 'package:astro_guide/l10n/generated/app_localizations.dart';

/// Responsive scaffold that adapts navigation based on screen width.
///
/// - Mobile (<600dp): Bottom Navigation Bar
/// - Desktop/Tablet (>=600dp): Navigation Rail
class ResponsiveScaffold extends StatelessWidget {
  /// Current route path for highlighting active nav item.
  final String currentPath;

  /// The main content child widget.
  final Widget child;

  const ResponsiveScaffold({
    super.key,
    required this.currentPath,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final isDesktop = width >= 600;

    final currentIndex = _getIndexFromPath(currentPath);

    if (isDesktop) {
      return _buildDesktopLayout(context, currentIndex);
    } else {
      return _buildMobileLayout(context, currentIndex);
    }
  }

  Widget _buildMobileLayout(BuildContext context, int currentIndex) {
    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(
            top: BorderSide(color: AppColors.surfaceElevated, width: 1),
          ),
        ),
        child: BottomNavigationBar(
          currentIndex: currentIndex,
          onTap: (index) => _onNavigate(context, index),
          items: [
            BottomNavigationBarItem(
              icon: FaIcon(FontAwesomeIcons.binoculars, size: 20),
              activeIcon: FaIcon(FontAwesomeIcons.binoculars, size: 20),
              label: AppLocalizations.of(context)!.navObservatory,
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.history_outlined),
              activeIcon: Icon(Icons.history),
              label: AppLocalizations.of(context)!.navLog,
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.auto_awesome_outlined),
              activeIcon: Icon(Icons.auto_awesome),
              label: AppLocalizations.of(context)!.navChat,
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.settings_outlined),
              activeIcon: Icon(Icons.settings),
              label: AppLocalizations.of(context)!.navSettings,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDesktopLayout(BuildContext context, int currentIndex) {
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: currentIndex,
            onDestinationSelected: (index) => _onNavigate(context, index),
            labelType: NavigationRailLabelType.all,
            leading: Padding(
              padding: const EdgeInsets.symmetric(vertical: 16),
              child: Icon(
                Icons.auto_awesome,
                color: AppColors.cyanAccent,
                size: 32,
              ),
            ),
            destinations: [
              NavigationRailDestination(
                icon: FaIcon(FontAwesomeIcons.binoculars, size: 20),
                selectedIcon: FaIcon(FontAwesomeIcons.binoculars, size: 20),
                label: Text(AppLocalizations.of(context)!.navObservatory),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.history_outlined),
                selectedIcon: Icon(Icons.history),
                label: Text(AppLocalizations.of(context)!.navLog),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.auto_awesome_outlined),
                selectedIcon: Icon(Icons.auto_awesome),
                label: Text(AppLocalizations.of(context)!.navChat),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.settings_outlined),
                selectedIcon: Icon(Icons.settings),
                label: Text(AppLocalizations.of(context)!.navSettings),
              ),
            ],
          ),
          const VerticalDivider(width: 1, thickness: 1),
          Expanded(child: child),
        ],
      ),
    );
  }

  int _getIndexFromPath(String path) {
    if (path.startsWith('/logbook')) return 1;
    if (path.startsWith('/chat')) return 2;
    if (path.startsWith('/settings')) return 3;
    return 0; // Default to observatory
  }

  void _onNavigate(BuildContext context, int index) {
    switch (index) {
      case 0:
        context.go('/observatory');
        break;
      case 1:
        context.go('/logbook');
        break;
      case 2:
        context.go('/chat');
        break;
      case 3:
        context.go('/settings');
        break;
    }
  }
}
