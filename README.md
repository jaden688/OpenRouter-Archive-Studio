# OpenRouter Archive Studio

**Turn your OpenRouter generation history into readable, searchable telemetry.**

OpenRouter Archive Studio is a local-first desktop application for retrieving, importing, inspecting, and analyzing your OpenRouter generation history. It organizes raw generation records and analytics into a workspace where you can investigate what happened, track usage, and uncover patterns that are difficult to see in raw API activity.

## What it does

- **Generation archive:** browse and search generation history, including prompts, completions, reasoning content, timestamps, and raw metadata when available.
- **Usage and telemetry explorer:** inspect the SQLite archive's analytics tables, choose visible columns, filter and sort records, paginate large datasets, and export selected data to CSV.
- **Model and provider analysis:** explore available hourly, daily, weekly, and monthly analytics, plus model, provider, application, API-key, token, cost, latency, and other breakdowns supplied by the source archive.
- **Archive import:** import compatible SQLite archives while preserving source files and skipping duplicate generation IDs.
- **Historical recovery:** retrieve generation IDs through OpenRouter analytics and fetch corresponding generation metadata/content for a selected date range. Requires an OpenRouter management key entered for the recovery session.
- **Optional translation:** translation is a separate, user-initiated workflow. Original source content remains preserved; the app does not automatically translate the archive.

## Run from source

Requirements: Python 3.10+ and PySide6.

```bash
python -m pip install -r requirements.txt
python OpenRouter_Translate_Viewer.py
```

The main window includes the **METRICS EXPLORER**. Keep `archive_metrics_explorer.py` beside the main application file.

Optional offline translation requires Argos Translate and a compatible installed Chinese-to-English language package. It is not required for archive browsing, recovery, or metrics exploration.

## Data and privacy

The application is local-first. Your archive is stored in a SQLite database alongside the application unless you choose another archive through the import workflow. Generation records can contain private prompts, responses, identifiers, and other sensitive content.

- Do not publish your personal SQLite database, exports, logs, backups, or credentials.
- Recovery credentials are requested for the recovery session and are not intended to be committed or stored in the source repository.
- Keep personal archive files outside the source repository. The included `.gitignore` excludes common database, log, backup, and secret file types.
- Translation is opt-in and separate from the original archived content.

## Project status

The working application includes archive browsing, SQLite import, OpenRouter historical recovery, and the metrics explorer. This repository is a source-code preview. Packaged installers, cross-platform release validation, and final distribution terms are not yet provided here.

## Scope

This project is specifically for **OpenRouter** generation history and analytics. It is not a generic multi-provider LLM observability platform.
