"""
Example script demonstrating Indonesian directory naming.

This script shows how the AI File Classifier uses Indonesian language
for directory names when configured with language.primary = "indonesian".
"""

# Language-specific examples (from AIClassifier)
LANGUAGE_EXAMPLES = {
    "indonesian": """- Documents → "Dokumen"
- Financial Reports → "Laporan Keuangan"
- Personal Photos → "Foto Pribadi"
- Work Projects → "Proyek Pekerjaan"
- Music → "Musik"
- Videos → "Video"
- Archives → "Arsip"
- Downloads → "Unduhan"
- Images → "Gambar"
- Spreadsheets → "Lembar Kerja"
- Presentations → "Presentasi"
- Code → "Kode Program"
- Books → "Buku"
- Contracts → "Kontrak"
- Invoices → "Faktur"
- Receipts → "Kwitansi"
- Tax Documents → "Dokumen Pajak"
- Annual Reports → "Laporan Tahunan"
- Meeting Notes → "Catatan Rapat"
- Research → "Penelitian"
""",
    "english": """- Documents → "Documents"
- Financial Reports → "Financial Reports"
- Personal Photos → "Personal Photos"
- Work Projects → "Work Projects"
- Music → "Music"
- Videos → "Videos"
- Archives → "Archives"
"""
}

SYSTEM_PROMPT_TEMPLATE = """You are an expert file organization assistant. Your task is to analyze file information and suggest appropriate directory classifications.

Rules:
1. Provide concise, meaningful directory names IN {language} LANGUAGE
2. Use hierarchical structure (parent/child) when appropriate
3. Avoid overly specific categories (max 3 levels deep)
4. Consider file content, name, and metadata
5. Return results in valid JSON format
6. ALL directory names (primary_category, subcategory, sub_subcategory) MUST be in {language}

Language-specific examples for {language}:
{examples}

Output format:
{{
  "primary_category": "string (in {language})",
  "subcategory": "string or null (in {language})",
  "sub_subcategory": "string or null (in {language})",
  "confidence": float (0.0-1.0),
  "reasoning": "string (can be in English)"
}}"""

def build_prompt(language: str) -> str:
    """Build system prompt for given language."""
    examples = LANGUAGE_EXAMPLES.get(language, LANGUAGE_EXAMPLES["english"])
    return SYSTEM_PROMPT_TEMPLATE.format(
        language=language.upper(),
        examples=examples
    )

def demonstrate_indonesian_prompts():
    """Demonstrate how Indonesian language configuration affects prompts."""

    print("="*70)
    print("Indonesian Directory Naming - Example System Prompts")
    print("="*70)
    print()

    # Example 1: Indonesian (Primary)
    print("1. INDONESIAN CONFIGURATION")
    print("-" * 70)
    print(build_prompt("indonesian"))
    print()
    print()

    # Example 2: English (Fallback)
    print("2. ENGLISH CONFIGURATION")
    print("-" * 70)
    print(build_prompt("english"))
    print()
    print()

    # Example 3: Directory name examples
    print("3. EXPECTED DIRECTORY NAME EXAMPLES")
    print("-" * 70)
    print()
    print("English → Indonesian Mapping:")
    print("  Documents           → Dokumen")
    print("  Financial Reports   → Laporan Keuangan")
    print("  Personal Photos     → Foto Pribadi")
    print("  Work Projects       → Proyek Pekerjaan")
    print("  Music               → Musik")
    print("  Videos              → Video")
    print("  Archives            → Arsip")
    print("  Downloads           → Unduhan")
    print("  Images              → Gambar")
    print("  Spreadsheets        → Lembar Kerja")
    print("  Code                → Kode Program")
    print("  Contracts           → Kontrak")
    print("  Invoices            → Faktur")
    print("  Tax Documents       → Dokumen Pajak")
    print()
    print("With snake_case naming convention:")
    print("  Laporan Keuangan    → laporan_keuangan/")
    print("  Foto Pribadi        → foto_pribadi/")
    print("  Proyek Pekerjaan    → proyek_pekerjaan/")
    print("  Kode Program        → kode_program/")
    print()
    print("="*70)

def show_configuration_guide():
    """Show how to configure Indonesian language in config.yaml."""

    print()
    print("="*70)
    print("CONFIGURATION GUIDE")
    print("="*70)
    print()
    print("To enable Indonesian directory naming, add this to config.yaml:")
    print()
    print("# Language Settings")
    print("language:")
    print("  primary: \"indonesian\"      # Primary language for directory names")
    print("  fallback: \"english\"        # Fallback if primary not available")
    print("  supported_languages:")
    print("    - \"indonesian\"")
    print("    - \"english\"")
    print("    - \"spanish\"")
    print("    - \"french\"")
    print()
    print("Available languages:")
    print("  - indonesian (Bahasa Indonesia)")
    print("  - english")
    print("  - spanish (Español)")
    print("  - french (Français)")
    print()
    print("Note: The classifier will automatically use the primary language")
    print("to generate directory names based on file content.")
    print()
    print("="*70)

def main():
    """Run the demonstration."""
    demonstrate_indonesian_prompts()
    show_configuration_guide()

if __name__ == "__main__":
    main()
