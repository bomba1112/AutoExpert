import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';

class LanguagePage extends StatefulWidget {
  const LanguagePage({required this.onSelected, this.initial = 'en', super.key});

  final ValueChanged<String> onSelected;
  final String initial;

  @override
  State<LanguagePage> createState() => _LanguagePageState();
}

class _LanguagePageState extends State<LanguagePage> {
  late String _selected = widget.initial;

  @override
  Widget build(BuildContext context) {
    final copy = AppLocalizations.of(context);
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 520),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const _BrandMark(),
                  const SizedBox(height: 32),
                  Text(copy.chooseLanguage,
                      style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 8),
                  Text(copy.languageCanChange,
                      style: Theme.of(context).textTheme.bodyLarge),
                  const SizedBox(height: 24),
                  for (final language in const [
                    ('en', 'English'),
                    ('az', 'Azərbaycan dili'),
                    ('ru', 'Русский'),
                  ])
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _LanguageTile(
                        code: language.$1,
                        label: language.$2,
                        selected: _selected == language.$1,
                        onTap: () => setState(() => _selected = language.$1),
                      ),
                    ),
                  const SizedBox(height: 18),
                  FilledButton(
                    onPressed: () => widget.onSelected(_selected),
                    child: Text(copy.continueLabel),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _BrandMark extends StatelessWidget {
  const _BrandMark();

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        width: 64,
        height: 64,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primary,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Icon(
          Icons.speed_rounded,
          color: Theme.of(context).colorScheme.secondary,
          size: 34,
        ),
      ),
    );
  }
}

class _LanguageTile extends StatelessWidget {
  const _LanguageTile({
    required this.code,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String code;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? const Color(0xFFE7EDF0) : Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: selected
              ? Theme.of(context).colorScheme.primary
              : const Color(0xFFE6E0D8),
          width: selected ? 1.5 : 1,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 17),
          child: Row(
            children: [
              Expanded(
                  child: Text(label,
                      style: Theme.of(context).textTheme.titleMedium)),
              Text(code.toUpperCase()),
              const SizedBox(width: 12),
              Icon(selected ? Icons.check_circle : Icons.circle_outlined),
            ],
          ),
        ),
      ),
    );
  }
}
