# Project Structure

```
├── main.py              # Application entry point, logging setup
├── __version__.py       # Version string
├── app_settings.json    # Runtime config (generated)
│
├── core/                # Business logic
│   ├── config_manager.py    # JSON config persistence
│   ├── log_collector.py     # Process log aggregation
│   ├── migration_manager.py # Config migration
│   ├── process_manager.py   # PMHQ/LLOneBot process lifecycle
│   ├── update_checker.py    # NPM registry version checks
│   ├── update_manager.py    # Update orchestration
│   └── version_detector.py  # Local version detection
│
├── ui/                  # Flet UI components
│   ├── main_window.py       # Main window, navigation
│   ├── home_page.py         # Dashboard/control panel
│   ├── log_page.py          # Log viewer
│   ├── config_page.py       # Settings page
│   ├── llonebot_config_page.py  # Bot-specific config
│   ├── about_page.py        # About/update page
│   ├── login_dialog.py      # QQ login dialog
│   ├── theme.py             # Theme management
│   └── animations.py        # UI animations
│
├── utils/               # Utilities
│   ├── constants.py         # App constants, defaults
│   ├── downloader.py        # File download helper
│   ├── github_api.py        # GitHub API client
│   ├── http_client.py       # HTTP request wrapper
│   ├── mirror_manager.py    # NPM/GitHub mirror selection
│   ├── npm_api.py           # NPM registry client
│   ├── port.py              # Port availability check
│   └── qq_path.py           # QQ installation detection
│
├── tests/               # pytest test files
│   └── test_*.py
│
├── bin/                 # Runtime binaries (downloaded)
│   ├── pmhq/
│   └── llonebot/
│
├── logs/                # Application logs (generated)
├── hooks/               # PyInstaller hooks
└── package/             # NPM package output
```

## Module Conventions
- Each module has `__init__.py` with Chinese docstring
- `core/` exports key classes via `__all__`
- UI pages follow pattern: class with `build()` method returning Flet control
- Tests mirror source structure: `test_<module>.py`
