# OpenRouter Archive Studio

A desktop SQLite viewer for OpenRouter generation logs, metadata, tool-call and reasoning transcripts, local translation, and imported analytics.

## Features
- Select models/generations and inspect individual conversation segments
- View raw metadata, original messages and tool calls
- Metrics Explorer with columns chosen per table and saved locally
- Browse all SQLite tables, paginate 150 records at a time, search, sort and export the visible page
- Full read-only inspector for individual database fields
- Global row numbers and clear page/scroll-position indicators
- Import compatible SQLite exports and recover historical generations (OpenRouter management API key entered at runtime)
- Optional offline Chinese-to-English translation using Argos Translate

## Linux setup
Install Python 3 and PySide6, then launch:

    python -m pip install -r requirements.txt
    python OpenRouter_Translate_Viewer.py

The current desktop application expects a local SQLite working copy named
openrouter-logs-EN-WORKING.sqlite next to the Python files. It is not included.
Use a trusted existing OpenRouter Archive Studio database with a generations
table, or adapt the viewer to your own SQLite schema.
An OpenRouter API or management key is never bundled or required merely to browse saved data.

Optional local translation expects a separate Argos Translate Python environment
at ~/.local/share/openrouter-translator-venv/ with the zh to en language package installed.
Browsing and metrics exploration do not require a translation model.

## Data privacy
This repository includes source code only.
Never add your .sqlite/.db files, database exports, translated records, archived prompts,
captures, backups, key material or logs to a public repository.
The .gitignore allowlists the five application source modules plus the documentation
and requirements. User-specific layout preferences are stored in metrics_layouts.json
and must remain local.

The explorer uses a read-only database connection. The main Archive Studio's import,
recovery, and translation features can write to its working database as intended.

## Known scope
This is a standalone desktop application and not the JL Engine runtime.
The current viewer reads an existing compatible archive; it does not generate one from scratch.
