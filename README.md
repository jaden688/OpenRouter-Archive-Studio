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

## Install and run

**Windows:** Install Python 3.10 or newer, extract the repository ZIP, and double-click Install-and-Run-Windows.bat. The script creates a private .venv, installs the required packages with pip, and launches the application.

**Linux:** Install Python 3.10 or newer (including your distribution's venv package), then run chmod +x install-and-run-linux.sh followed by ./install-and-run-linux.sh.

Both launchers keep Python packages in a .venv inside the application folder. They do not modify the system Python environment. The first run downloads PySide6 and its Qt dependencies; this is a sizeable download. Later launches reuse the environment.

To run the test suite, use python -m unittest discover -s tests -v.

Manual installation: create a virtual environment with python -m venv .venv, activate it, run python -m pip install --upgrade pip, then python -m pip install -r requirements.txt and python OpenRouter_Translate_Viewer.py. On Windows activate with .venv\Scripts\Activate.ps1; on Linux use source .venv/bin/activate.

The first launch creates an empty local SQLite archive automatically. Use IMPORT DATABASE to load an existing compatible archive, or IMPORT / RECOVER to retrieve history through OpenRouter using a management key. The app does not ship with anyone's personal archive.

Optional offline translation is separate. Install requirements-translation.txt into the same .venv, then install a compatible Argos Translate Chinese-to-English language package. Translation remains user-initiated and is never run automatically. Original source content remains preserved.

## Data and privacy

The application is local-first. Your archive is stored in a SQLite database alongside the application unless you choose another archive through the import workflow. Generation records can contain private prompts, responses, identifiers, and other sensitive content.

- Do not publish your personal SQLite database, exports, logs, backups, or credentials.
- Recovery credentials are requested for the recovery session and are not intended to be committed or stored in the source repository.
- Keep personal archive files outside the source repository. The included `.gitignore` excludes common database, log, backup, and secret file types.
- Translation is opt-in and separate from the original archived content.

## Project status

The working application includes archive browsing, SQLite import, OpenRouter historical recovery, and the metrics explorer. This repository is a source-code preview. The repository includes Python-based first-run launchers for Windows and Linux. The included test suite covers fresh database initialization and GUI startup. Native packaged installers and final distribution terms are not yet provided here.

## Scope

This project is specifically for **OpenRouter** generation history and analytics. It is not a generic multi-provider LLM observability platform.
