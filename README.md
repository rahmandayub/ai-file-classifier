# AI File Classifier

A Python-based intelligent application that automatically analyzes, classifies, and organizes files into well-structured directory hierarchies using Large Language Models (LLMs) through OpenAI-compatible APIs.

## Features

- **AI-Powered Classification**: Uses LLMs to intelligently understand file content and context
- **Multi-Language Directory Naming**: Generate directory names in Indonesian, English, Spanish, French, and more
- **Multiple AI Provider Support**: Works with OpenAI, Ollama, LocalAI, and other OpenAI-compatible APIs
- **Flexible Organization**: Content-based, project-based, date-based, and type-based classification strategies
- **Dry-Run Mode**: Preview changes before executing
- **Intelligent Caching**: Reduces redundant API calls and improves performance
- **Comprehensive Reporting**: JSON, CSV, and HTML reports with detailed statistics
- **Configurable**: Extensive YAML configuration with sensible defaults
- **Safe Operations**: File verification, rollback capability, and duplicate handling

## Requirements

- Python 3.10 or higher
- OpenAI API key (for OpenAI) or local LLM server (Ollama, LocalAI)

## Quick Install

### Automated Setup (Recommended)

**Linux/macOS:**
```bash
git clone https://github.com/yourusername/ai-file-classifier.git
cd ai-file-classifier
./setup.sh
```

**Windows:**
```cmd
git clone https://github.com/yourusername/ai-file-classifier.git
cd ai-file-classifier
setup.bat
```

The setup script will automatically:
- Check Python version (3.10+)
- Create virtual environment
- Install dependencies
- Create `.env` file from template
- Verify installation

### Manual Setup

```bash
# Clone repository
git clone https://github.com/yourusername/ai-file-classifier.git
cd ai-file-classifier

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install
pip install --upgrade pip
pip install -e .

# Verify
python -m src.main --version
```

## Installation

### Prerequisites

Modern Python installations require using virtual environments. Ensure you have Python 3.10 or higher installed:

```bash
python3 --version  # Should be 3.10 or higher
```

### From Source (Recommended)

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-file-classifier.git
cd ai-file-classifier
```

#### 2. Create and Activate Virtual Environment

**On Linux/macOS:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

**On Windows:**
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

#### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install the package in editable mode
pip install -e .
```

#### 4. Verify Installation

```bash
python -m src.main --version
```

### Using pip (When Available)

```bash
# Create and activate virtual environment first (see above)
pip install ai-file-classifier
```

### Deactivating Virtual Environment

When you're done, deactivate the virtual environment:

```bash
deactivate
```

## Quick Start

### 1. Set Up API Configuration

Create a `.env` file (or set environment variables):

**For OpenAI:**
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# OPENAI_API_KEY=your_openai_api_key_here
```

**For Ollama (Local LLM - No API Key Required):**
```bash
# Install Ollama from https://ollama.ai
ollama serve

# Pull a model
ollama pull gemma3:latest
```

The default configuration uses Ollama, so no API key is needed if you're running Ollama locally.

### 2. Basic Usage

**Make sure your virtual environment is activated** (you should see `(venv)` in your terminal):

```bash
# Classify files in a directory (uses config.yaml language setting, default: English)
python -m src.main classify /path/to/messy/files /path/to/organized/files

# Use Indonesian for directory names (override config)
python -m src.main classify /path/to/files /path/to/organized --language id

# Use English for directory names (override config)
python -m src.main classify /path/to/files /path/to/organized --language en

# Preview changes without moving files (dry run)
python -m src.main classify /path/to/files /path/to/organized --dry-run

# Use custom configuration
python -m src.main classify /path/to/files /path/to/organized --config config/config.yaml

# Verbose output
python -m src.main classify /path/to/files /path/to/organized --verbose
```

#### Language Options

You can specify the language using either short codes or full names:

| Short Code | Full Name | Example |
|------------|-----------|---------|
| `id` | `indonesian` | `--language id` |
| `en` | `english` | `--language en` |
| `es` | `spanish` | `--language es` |
| `fr` | `french` | `--language fr` |
| `de` | `german` | `--language de` |
| `ja` | `japanese` | `--language ja` |
| `zh` | `chinese` | `--language zh` |

## Configuration

The application uses a YAML configuration file. See `config/config.yaml` for a complete example.

### Key Configuration Sections

#### API Configuration

```yaml
api:
  provider: "ollama"  # openai, ollama, localai, custom
  api_key: "${OPENAI_API_KEY}"
  base_url: "http://localhost:11434/v1"
  model_name: "gemma3:latest"
  temperature: 0.2
  max_tokens: 1000
```

#### Classification Settings

```yaml
classification:
  default_strategy: "content_based"
  confidence_threshold: 0.5
  max_depth: 3
```

#### File Scanning

```yaml
scanning:
  recursive: true
  ignore_hidden: true
  ignore_patterns:
    - "node_modules"
    - ".git"
    - "__pycache__"
```

## Usage Examples

### Example 1: Organize Downloads Folder with Indonesian Names

```bash
# Preview with Indonesian directory names
python -m src.main classify ~/Downloads ~/Downloads/Organized --language id --dry-run

# Results: dokumen/, gambar/, musik/, video/, etc.
```

### Example 2: Classify Code Projects with English Names

```bash
# Organize with English directory names
python -m src.main classify ~/Projects ~/Projects/Organized --language en

# Results: documents/, images/, music/, videos/, etc.
```

### Example 3: Using Spanish for Personal Files

```bash
# Use Spanish directory names
python -m src.main classify ~/Documents ~/Documents/Organized --language es

# Results: documentos/, fotos_personales/, etc.
```

### Example 4: Using Ollama (Local LLM)

1. Install and start Ollama:
```bash
ollama serve
ollama pull gemma3:latest
```

2. Update `config/config.yaml`:
```yaml
api:
  provider: "ollama"
  base_url: "http://localhost:11434/v1"
  model_name: "gemma3:latest"
```

3. Run classifier with language preference:
```bash
# Indonesian directories with local LLM
python -m src.main classify /path/to/files /path/to/organized --language id

# English directories with local LLM
python -m src.main classify /path/to/files /path/to/organized --language en
```

## Directory Structure After Classification

The AI will create an intelligent directory structure based on file content. For example:

```
organized/
├── documents/
│   ├── reports/
│   ├── invoices/
│   └── contracts/
├── code/
│   ├── python_projects/
│   ├── javascript_projects/
│   └── scripts/
├── media/
│   ├── photos/
│   ├── videos/
│   └── audio/
└── data/
    ├── spreadsheets/
    └── datasets/
```

## Naming Conventions

The classifier supports multiple naming conventions:

- `snake_case` (default): `my_project_files`
- `kebab-case`: `my-project-files`
- `PascalCase`: `MyProjectFiles`
- `camelCase`: `myProjectFiles`

Configure in `config.yaml`:

```yaml
directories:
  naming_convention: "snake_case"
```

## Multi-Language Directory Naming

The AI File Classifier supports generating directory names in multiple languages. **English is the default**, but you can easily switch to Indonesian, Spanish, French, or other supported languages using the `--language` CLI argument.

### Supported Languages

- **English** (Default)
- **Indonesian** (Bahasa Indonesia)
- Spanish (Español)
- French (Français)
- German (Deutsch)
- Japanese (日本語)
- Chinese (中文)

### Configuration

There are two ways to set the language:

#### Option 1: Command-Line Argument (Recommended)

Use the `--language` or `-l` flag when running the classifier:

```bash
# Indonesian
python -m src.main classify ./files ./organized --language id

# English (default if no config and no argument)
python -m src.main classify ./files ./organized --language en

# Spanish
python -m src.main classify ./files ./organized --language es
```

**Supported language codes:**
- `id` or `indonesian` - Bahasa Indonesia
- `en` or `english` - English (default)
- `es` or `spanish` - Español
- `fr` or `french` - Français
- `de` or `german` - Deutsch
- `ja` or `japanese` - 日本語
- `zh` or `chinese` - 中文

#### Option 2: Configuration File

Add the language configuration to your `config/config.yaml`:

```yaml
# Language Settings
language:
  primary: "indonesian"      # Primary language for directory names
  fallback: "english"        # Fallback if primary not available
  supported_languages:
    - "indonesian"
    - "english"
    - "spanish"
    - "french"
```

**Note:** The `--language` CLI argument will override the config file setting.

### Examples

#### Indonesian Directory Names (Default)

When configured with Indonesian as the primary language, the classifier will generate directory names like:

```
organized/
├── dokumen/
│   ├── laporan_keuangan/
│   ├── faktur/
│   └── kontrak/
├── kode_program/
│   ├── proyek_python/
│   └── skrip/
├── media/
│   ├── foto_pribadi/
│   ├── video/
│   └── musik/
└── data/
    ├── lembar_kerja/
    └── arsip/
```

**Common Indonesian → English Translations:**

| Indonesian | English | snake_case Output |
|------------|---------|-------------------|
| Dokumen | Documents | `dokumen/` |
| Laporan Keuangan | Financial Reports | `laporan_keuangan/` |
| Foto Pribadi | Personal Photos | `foto_pribadi/` |
| Proyek Pekerjaan | Work Projects | `proyek_pekerjaan/` |
| Musik | Music | `musik/` |
| Video | Videos | `video/` |
| Arsip | Archives | `arsip/` |
| Unduhan | Downloads | `unduhan/` |
| Gambar | Images | `gambar/` |
| Lembar Kerja | Spreadsheets | `lembar_kerja/` |
| Kode Program | Code | `kode_program/` |
| Kontrak | Contracts | `kontrak/` |
| Faktur | Invoices | `faktur/` |
| Dokumen Pajak | Tax Documents | `dokumen_pajak/` |

#### English Directory Names

```yaml
language:
  primary: "english"
```

```
organized/
├── documents/
│   ├── financial_reports/
│   ├── invoices/
│   └── contracts/
├── code/
│   ├── python_projects/
│   └── scripts/
└── media/
    ├── personal_photos/
    ├── videos/
    └── music/
```

### Testing Language Configuration

Run the included example to see how different languages affect directory naming:

```bash
python examples/indonesian_example.py
```

This will display:
- System prompts for Indonesian and English configurations
- Example directory name mappings
- Configuration instructions

### How It Works

1. **AI Analysis**: The LLM analyzes file content in any language
2. **Category Generation**: Based on the configured language, it generates appropriate category names
3. **Naming Convention**: The naming convention (snake_case, kebab-case, etc.) is applied to the generated names
4. **Directory Creation**: Directories are created with the localized names

**Example Flow:**

```
File: budget_2024.xlsx
    ↓
AI Analysis (understands content in any language)
    ↓
Category Generation (in Indonesian): "Dokumen Keuangan" → "Anggaran"
    ↓
Apply Naming Convention: "dokumen_keuangan/anggaran/"
    ↓
Final Path: organized/dokumen_keuangan/anggaran/budget_2024.xlsx
```

### Benefits of Multi-Language Support

- **Localization**: Organize files in your native language
- **Clarity**: Directory names that make sense to local users
- **Flexibility**: Switch languages easily via configuration
- **AI-Powered**: Intelligent translation and categorization

## Reports

After execution, reports are generated in the `reports/` directory:

- **JSON Report**: Detailed classification data
- **CSV Report**: Tabular data for analysis
- **HTML Report**: Visual summary with statistics

## Advanced Features

### Caching

The classifier caches AI responses to avoid redundant API calls:

```yaml
app:
  cache_enabled: true
  cache_dir: ".cache"
  cache_ttl_hours: 24
```

### Duplicate Handling

Configure how to handle duplicate filenames:

```yaml
operations:
  duplicate_handling: "rename"  # skip, rename, overwrite
  rename_pattern: "{name}_{counter}{ext}"
```

### File Filters

Filter files by extension, size, or date:

```yaml
scanning:
  file_filters:
    extensions:
      exclude: [".exe", ".dll", ".so"]
    size:
      max_bytes: 104857600  # 100 MB
```

## Development

### Setting Up Development Environment

1. **Clone and set up virtual environment** (see Installation section above)

2. **Install development dependencies:**

```bash
# Make sure virtual environment is activated
pip install -e ".[dev]"
```

### Running Tests

```bash
# Ensure virtual environment is activated
pytest

# With coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_file_scanner.py -v
```

### Code Structure

```
ai-file-classifier/
├── src/
│   ├── core/              # Core modules
│   ├── strategies/        # Classification strategies
│   ├── models/            # Data models
│   ├── utils/             # Utilities
│   ├── app_controller.py  # Main orchestrator
│   ├── cli.py             # CLI interface
│   └── main.py            # Entry point
├── config/                # Configuration files
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Troubleshooting

### Common Issues

1. **"externally-managed-environment" error**:
   - **Solution**: Always use a virtual environment (see Installation section)
   - This error occurs when trying to install packages globally on modern Python installations

2. **Virtual environment not activated**:
   - **Solution**: Run `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
   - Check for `(venv)` in your terminal prompt

3. **API Connection Error**:
   - Check your API key and base URL
   - For Ollama: ensure `ollama serve` is running

4. **Rate Limiting**:
   - Adjust `requests_per_minute` in config
   - Consider using a local LLM (Ollama) for unlimited requests

5. **Out of Memory**:
   - Reduce `batch_size` and `max_workers` in config
   - Reduce `max_content_length` for large files

6. **Permission Denied**:
   - Ensure you have write access to destination directory
   - Try running with appropriate permissions

### Enable Debug Logging

```bash
python -m src.main classify /path/to/files /path/to/organized --verbose
```

## Performance

- Processes 100+ files per minute (excluding API latency)
- Concurrent API requests for improved throughput
- Intelligent caching reduces API calls by 60%+
- Memory efficient (<500MB for 10,000 files)

## Security

- API keys stored in environment variables
- No sensitive data logged
- File permissions preserved
- Path validation prevents directory traversal

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [OpenAI Python SDK](https://github.com/openai/openai-python)
- Supports [Ollama](https://ollama.ai/) for local LLM deployment
- Inspired by the need for intelligent file organization

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/ai-file-classifier/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/ai-file-classifier/discussions)

---

**Note**: This tool uses AI for classification. While generally accurate, always review the dry-run output before executing file moves.
