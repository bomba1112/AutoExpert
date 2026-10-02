/// US VINs use the ninth character as a check digit.
/// This is a local input check; the server remains authoritative.
bool isValidUsVin(String input) {
  final vin = input.trim().toUpperCase();
  if (!RegExp(r'^[A-HJ-NPR-Z0-9]{17}$').hasMatch(vin)) return false;

  const values = <String, int>{
    'A': 1,
    'B': 2,
    'C': 3,
    'D': 4,
    'E': 5,
    'F': 6,
    'G': 7,
    'H': 8,
    'J': 1,
    'K': 2,
    'L': 3,
    'M': 4,
    'N': 5,
    'P': 7,
    'R': 9,
    'S': 2,
    'T': 3,
    'U': 4,
    'V': 5,
    'W': 6,
    'X': 7,
    'Y': 8,
    'Z': 9,
  };
  const weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2];
  var sum = 0;
  for (var index = 0; index < vin.length; index++) {
    final character = vin[index];
    final value = int.tryParse(character) ?? values[character];
    if (value == null) return false;
    sum += value * weights[index];
  }
  final remainder = sum % 11;
  return vin[8] == (remainder == 10 ? 'X' : '$remainder');
}
