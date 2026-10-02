import 'package:autoexpert_client/app/app.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('starts at language selection', (tester) async {
    await tester.pumpWidget(const AutoExpertApp());
    await tester.pumpAndSettle();

    expect(find.text('Azərbaycan dili'), findsOneWidget);
    expect(find.text('Русский'), findsOneWidget);
    expect(find.text('English'), findsOneWidget);
  });
}
