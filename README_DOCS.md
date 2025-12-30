# Documentation Setup

This repository uses [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/) for documentation, and is configured for deployment on [Read the Docs](https://readthedocs.org/).

## Local Development

To build and preview the documentation locally:

```bash
# Install documentation dependencies
pip install -r docs/requirements.txt

# Serve documentation locally (with live reload)
mkdocs serve

# Build documentation
mkdocs build
```

The documentation will be available at `http://127.0.0.1:8000` when using `mkdocs serve`.

## Read the Docs Configuration

The repository is configured for Read the Docs deployment via `.readthedocs.yaml`:

- **Build system**: MkDocs
- **Python version**: 3.11
- **Documentation formats**: HTML, PDF, EPUB

### Setting up on Read the Docs

1. Go to [Read the Docs](https://readthedocs.org/) and import your repository
2. The configuration in `.readthedocs.yaml` will be automatically detected
3. Read the Docs will build and host your documentation automatically

### Documentation Structure

- `docs/` - All documentation source files (Markdown)
- `mkdocs.yml` - MkDocs configuration
- `.readthedocs.yaml` - Read the Docs build configuration
- `docs/requirements.txt` - Documentation dependencies

## Documentation Files

- `index.md` - Homepage and overview
- `getting-started.md` - Installation and quick start
- `basic-usage.md` - Core usage patterns
- `json-parsing.md` - JSON parsing features
- `regex-parsing.md` - Regex pattern matching
- `error-handling.md` - Error handling and recovery
- `fastapi-integration.md` - FastAPI integration guide
- `advanced-patterns.md` - Advanced usage patterns
- `api-reference.md` - Complete API documentation

