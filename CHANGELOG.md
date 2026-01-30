# Changelog

All notable changes to this project are documented in this file.

## [Unreleased] - 2026-01-29

### Changed
- Converted naive UTC datetimes to timezone-aware UTC across the codebase (`datetime.now(timezone.utc)`).
- Updated SQLAlchemy `DateTime` columns to use `DateTime(timezone=True)` where appropriate to preserve tzinfo.
- Updated generated Nginx timestamps and monitoring endpoints to include explicit UTC offsets.
- Documentation updated to recommend timezone-aware datetimes and bump Python requirement to 3.11.

### Added
- Unit tests for timezone handling: `tests/test_timezones.py`.

### Removed
- Removed debug artifacts created during E2E troubleshooting: `playwright_debug_page.html`, `playwright_debug_screenshot.png`.

### Notes
- Run the test suite after pulling these changes to ensure your environment's DB driver preserves tzinfo (SQLite may return naive datetimes; tests accept that by treating them as UTC).
