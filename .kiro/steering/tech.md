# Tech Stack

## Language & Runtime
- Python 3.9+
- Package manager: `uv` (preferred) or pip

## Core Dependencies
- `flet` / `flet-desktop` >= 0.80.0 - Cross-platform UI framework
- `psutil` - System/process monitoring
- `pystray` + `pillow` - System tray integration
- `packaging` - Version comparison
- `PyInstaller` - Executable packaging

## Testing
- `pytest` - Test framework
- `hypothesis` - Property-based testing
- `pytest-asyncio` - Async test support

## Build System
- `setuptools` via pyproject.toml
- PyInstaller for Windows executable

## Common Commands

```bash
# Install dependencies
uv sync

# Run application
uv run python main.py

# Run tests
uv run pytest

# Run specific test file
uv run pytest tests/test_main.py -v

# Build executable
build.bat
# Or manually:
uv run pyinstaller lucky-lillia-desktop.spec

# Clean build artifacts
rmdir /s /q build dist
```

## Configuration Files
- `pyproject.toml` - Project metadata and dependencies
- `requirements.txt` - Pip-compatible dependencies
- `lucky-lillia-desktop.spec` - PyInstaller build config
- `app_settings.json` - Runtime configuration (generated)
