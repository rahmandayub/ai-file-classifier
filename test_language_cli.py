"""Test script to verify language CLI argument logic."""

def normalize_language_code(language: str) -> str:
    """
    Normalize language code to full language name.

    Args:
        language: Language code or full name

    Returns:
        Normalized language name
    """
    language_map = {
        'id': 'indonesian',
        'indonesian': 'indonesian',
        'en': 'english',
        'english': 'english',
        'es': 'spanish',
        'spanish': 'spanish',
        'fr': 'french',
        'french': 'french',
        'de': 'german',
        'german': 'german',
        'ja': 'japanese',
        'japanese': 'japanese',
        'zh': 'chinese',
        'chinese': 'chinese'
    }

    normalized = language_map.get(language.lower())
    if not normalized:
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Supported: id/indonesian, en/english, es/spanish, fr/french, de/german, ja/japanese, zh/chinese"
        )
    return normalized


def test_language_normalization():
    """Test language code normalization."""

    print("Testing Language Code Normalization")
    print("=" * 60)

    test_cases = [
        ("id", "indonesian"),
        ("indonesian", "indonesian"),
        ("en", "english"),
        ("english", "english"),
        ("es", "spanish"),
        ("spanish", "spanish"),
        ("fr", "french"),
        ("french", "french"),
        ("de", "german"),
        ("german", "german"),
        ("ja", "japanese"),
        ("japanese", "japanese"),
        ("zh", "chinese"),
        ("chinese", "chinese"),
        ("ID", "indonesian"),  # Test case insensitivity
        ("EN", "english"),
        ("SPANISH", "spanish"),
    ]

    passed = 0
    failed = 0

    for input_lang, expected in test_cases:
        try:
            result = normalize_language_code(input_lang)
            if result == expected:
                print(f"✓ '{input_lang}' -> '{result}'")
                passed += 1
            else:
                print(f"✗ '{input_lang}' -> '{result}' (expected: '{expected}')")
                failed += 1
        except Exception as e:
            print(f"✗ '{input_lang}' raised exception: {e}")
            failed += 1

    # Test invalid language
    print()
    print("Testing Invalid Language:")
    try:
        normalize_language_code("invalid")
        print("✗ Should have raised error for 'invalid'")
        failed += 1
    except Exception as e:
        print(f"✓ Correctly raised error for 'invalid': {type(e).__name__}")
        passed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print()

    # Show example CLI usage
    print("Example CLI Usage:")
    print("-" * 60)
    print("# Use Indonesian")
    print("python -m src.main classify ./files ./organized --language id")
    print()
    print("# Use English (default)")
    print("python -m src.main classify ./files ./organized --language en")
    print()
    print("# Use Spanish")
    print("python -m src.main classify ./files ./organized --language es")
    print()
    print("# No language specified (uses config, default: english)")
    print("python -m src.main classify ./files ./organized")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    import sys
    success = test_language_normalization()
    sys.exit(0 if success else 1)
