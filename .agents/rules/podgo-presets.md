---
trigger: model_decision
description: Rules for creating or editing Line 6 POD Go (.pgp) presets
---

# POD Go Preset Generation

When creating, editing, or troubleshooting `.pgp` presets:

1. **Never guess `@model` IDs or `.pgp` structure from memory.** Line 6 model IDs require exact suffixes (such as `Mono`, `Stereo`, `StereoV2`, or `1`).
2. **Use the local catalog and schema** in `.venv/lib/python3.12/site-packages/tonemaker/data/models.json` (or `tonemaker/data/knowledge/TONEMAKER_LLM_CONTEXT.md`) and reference presets in `data/Presets/`—or generate presets via the installed `tonemaker` package.
3. **Ensure valid `.pgp` structure:**
   - Top-level `"schema": "L6Preset"` and `"version": 6`.
   - Preset `"name"` (and `"comment"`/`"designer"`) must live under `data.meta`, never `data.tone.meta`.
   - `data.tone.dsp0` must use `"input"`, `"output"`, and all 10 block slots `block0`–`block9` (use `"@model": null` for empty slots).
4. **Validate the entire `.pgp` file before finishing** by running:
   ```bash
   QT_QPA_PLATFORM=offscreen .venv/bin/python -c "from PySide6.QtWidgets import QApplication; from pathlib import Path; from openpodgo.preset import load_pgp; from openpodgo.editor import PresetEditor; from openpodgo.ui.editor import EditorView; app = QApplication([]); pgp = load_pgp(Path('<file>.pgp')); ed, w = PresetEditor.from_pgp(pgp); assert not w, w; assert len(ed.preset.chain) == 10; assert pgp.get('data', {}).get('meta', {}).get('name'); assert EditorView().load_pgp(pgp); ed.to_blob()"
   ```
