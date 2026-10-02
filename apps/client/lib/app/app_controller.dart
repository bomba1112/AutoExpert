import 'package:flutter/material.dart';

class AppController extends ChangeNotifier {
  Locale? _locale;
  final List<String> _comparisonIds = [];

  Locale? get locale => _locale;
  List<String> get comparisonIds => List.unmodifiable(_comparisonIds);

  void addComparison(String variantId) {
    if (_comparisonIds.contains(variantId)) return;
    if (_comparisonIds.length >= 3) _comparisonIds.removeAt(0);
    _comparisonIds.add(variantId);
    notifyListeners();
  }

  void removeComparison(String variantId) {
    _comparisonIds.remove(variantId);
    notifyListeners();
  }

  void selectLanguage(String languageCode) {
    _locale = Locale(languageCode);
    notifyListeners();
  }

  void resetLanguage() {
    _locale = null;
    notifyListeners();
  }
}
