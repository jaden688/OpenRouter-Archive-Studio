# Publication checklist

## Product identity

- Product: OpenRouter Archive Studio
- One-line pitch: Turn your OpenRouter generation history into readable, searchable telemetry.
- Category: Developer Tools / Analytics
- Scope: OpenRouter only

## Source publication

- [x] Sync the current working viewer, metrics explorer, recovery, import, and translation modules into this source tree.
- [x] Update the README to describe the current feature set and local-first privacy model.
- [x] Keep personal SQLite archives, exports, credentials, logs, and backups out of version control.
- [x] Confirm repository owner/name and attach the correct Git remote.
- [x] Publish the source repository as public after reviewing the tracked file list and private database exclusion.
- [ ] Create a tagged source release after CI and clean-environment tests pass.

## Launch directory / PostYourStartup

- [ ] Provide a public product destination. A public source repository can be used as an interim destination if no hosted landing page exists; it is not a hosted demo.
- [ ] Add product logo and genuine screenshots of the running application.
- [ ] Confirm the free launch badge requirement and available launch slot on PostYourStartup.
- [ ] Submit the listing and verify the published page.

## Release validation

- [x] Run clean Python environment installation and GUI smoke tests on Linux.
- [ ] Validate the Windows first-run launcher on Windows.
- [ ] Verify SQLite import, archive browsing, metrics explorer, filtering, pagination, and CSV export.
- [ ] Test date-range recovery with a separate test archive and valid OpenRouter management key.
- [ ] Validate Windows and Linux packaging before offering installers.
- [ ] Verify optional translation separately; it must remain opt-in.

## Privacy gate

- [x] Inspect the published source diff for accidental personal data or secrets.
- [x] Confirm no personal archive database or exported generation content is tracked.
