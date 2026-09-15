# README screenshots

Captured on **2026-09-15**, on a Mac running macOS 26.6.2.

- PAIDEIA-Hermes: 0.4.0, source baseline `cbea9cc`.
- Hermes Agent: 0.20.0 (2026.8.3), Python 3.11.14.
- Display: the real `hermes chat --cli` process in a loopback-only ttyd 1.7.7 browser terminal, at 1280 × 720. These are unedited CLI captures, not interface mockups or messaging-gateway screenshots.
- Profile: an isolated `HERMES_HOME` with this plugin enabled. The active course was a synthetic complex-analysis demo, with a 2026-12-15 exam date.

| File | Actual command |
|------|----------------|
| `terminal-help.png` | `/paideia help` |
| `terminal-init.png` | `/paideia init name="Complex Analysis README demo" exam=2026-12-15 type=final lang=en ocr=claude weak=residues` |
| `terminal-doctor.png` | `/paideia doctor` |
| `terminal-status.png` | `/paideia status` |

The init capture repeats setup in an already-created demonstration course, hence “created 0 dirs.” The status remains `setup` because an analyzed pattern index was not produced. `doctor` reports local dependency/configuration checks; it does not prove a successful model request. Separately, a real agent-driven Markdown ingest copied the three demonstration source files, while the subsequent analyze request failed after provider connection retries. No generated-analysis or handwriting-accuracy claim is made by these images.

The README's hero reuses `terminal-help.png`. The original PAIDEIA's public interactive demo is labeled separately in the README.
