import 'package:flutter_test/flutter_test.dart';
import 'package:pyvault/main.dart';

void main() {
  testWidgets('PyVault app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const PyVaultApp());
    expect(find.text('PyVault'), findsOneWidget);
  });
}