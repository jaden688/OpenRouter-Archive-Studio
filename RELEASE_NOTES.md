# Unreleased preview update

This source preview now reflects the current working OpenRouter Archive Studio application rather than the earlier archive-browser-only snapshot.

## Included

- Windows and Linux first-run launchers that create an isolated Python environment and install dependencies with pip.
- Automatic creation of a valid empty SQLite archive on first launch.
- A test suite covering source compilation, fresh database initialization, and GUI startup.

- OpenRouter generation history browsing and inspection.
- SQLite archive import with duplicate generation ID handling and source preservation.
- Date-range historical recovery using OpenRouter analytics and generation endpoints.
- Read-only metrics explorer for browsing archive tables, selecting columns, filtering, sorting, paginating, and exporting CSV.
- Optional, explicitly user-initiated translation workflow that keeps original archived content intact.

## Not included / not claimed

- No hosted web application or public SaaS endpoint is included.
- No native MSI/EXE or AppImage package is provided; use the included Python-based launchers.
- No automatic translation of the archive.
- No support for providers other than OpenRouter is claimed.

Personal archives, credentials, logs, and backups are excluded from the repository.
