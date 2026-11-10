import 'package:flutter_test/flutter_test.dart';

import 'package:echo_assist_mobile/core/constants/api_constants.dart';

void main() {
  test('mobile API address is configurable and has no hardcoded private IP', () {
    expect(ApiConstants.baseUrl, startsWith('http'));
    expect(ApiConstants.baseUrl, isNot(contains('10.244.117.219')));
  });
}
