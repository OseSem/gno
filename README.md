# gno

**Interactive CLI tool for building .gitignore files**

gno (pronounced "noh") helps you create `.gitignore` files interactively with a beautiful split-pane TUI interface. It fetches templates from GitHub's official [gitignore repository](https://github.com/github/gitignore) and caches them locally for fast access.

## Features

- **Interactive TUI** - Split-pane interface with live preview
- **230+ Templates** - All templates from GitHub's gitignore repository
- **Smart Search** - Filter templates by name or description
- **Smart Merging** - Append to existing files without duplicates
- **Offline Support** - Templates cached locally after first fetch
- **Multiple Output Modes** - Interactive, generate, preview

## Installation

```bash
# Using uv (recommended)
uv tool install gno

# Or run directly without installing
uvx gno

# Using pipx
pipx install gno

# Using pip
pip install gno
```

## Usage

### Interactive Mode

Launch the TUI by running `gno` without arguments:

```bash
gno
```

**Controls:**
- `Up/Down` or `j/k` - Navigate templates
- `Space` - Toggle selection
- `/` - Search templates
- `s` - Save and exit
- `?` - Show help
- `q` - Quit

### Command Line

```bash
# Generate .gitignore from templates
gno generate python node

# Preview without saving
gno generate python --preview

# Save to custom path
gno generate rust -o backend/.gitignore

# Append to existing file (smart merge)
gno generate go --append

# List all templates
gno list

# Search templates
gno list python

# Show template content
gno show python

# Update template cache
gno update
```

## Examples

### Create a Python project .gitignore

```bash
gno generate python
```

### Create a full-stack project .gitignore

```bash
gno generate python node
```

### Add templates to existing .gitignore

```bash
gno generate terraform --append
```

## Template Sources

Templates are fetched from:
- [github/gitignore](https://github.com/github/gitignore) - Root directory (language templates)
- [github/gitignore/Global](https://github.com/github/gitignore/tree/main/Global) - Global templates (editors, OS, etc.)
- [github/gitignore/community](https://github.com/github/gitignore/tree/main/community) - Community templates (community-contributed templates)

## Cache

Templates are cached in `~/.gno/templates.json` for offline access and faster startup. Run `gno update` to refresh the cache.

## Development

```bash
# Clone the repository
git clone https://github.com/OseSem/gno
cd gno

# Install dependencies
uv sync

# Run the CLI
uv run gno

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run black --check .
```

## License

MIT License - see [LICENSE](LICENSE) for details.
