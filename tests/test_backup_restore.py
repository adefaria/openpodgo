"""Tests for backup and restore (.pgb) and preset archive (.zip) operations.

Covers TDD contract for writing and reading .pgb containers and .zip bundles.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from openpodgo import pgb

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_preset() -> dict:
    pgp_file = FIXTURES / "spec02_a.pgp"
    if pgp_file.exists():
        data = json.loads(pgp_file.read_bytes())
        return data["data"]
    return {
        "device": 2162695,
        "device_version": 33619968,
        "meta": {"name": "TestTone", "application": "openpodgo"},
        "tone": {"dsp0": {}, "global": {}},
    }


def test_write_and_read_backup_roundtrip(tmp_path: Path, sample_preset: dict):
    """Writing a Backup object to a .pgb produces a valid AF6L container that read_backup can load."""
    out_file = tmp_path / "device_backup.pgb"
    globals_data = {"System": {"device": 2162695, "version": "v2.01"}}
    factory_presets = [dict(sample_preset) for _ in range(4)]
    user_presets = [dict(sample_preset) for _ in range(4)]

    original_backup = pgb.Backup(
        globals=globals_data,
        setlists={
            "Factory": factory_presets,
            "User": user_presets,
        },
    )

    pgb.write_backup(out_file, original_backup)

    assert out_file.exists()
    content = out_file.read_bytes()
    assert content[:4] == pgb.MAGIC

    loaded = pgb.read_backup(out_file)
    assert loaded.globals == globals_data
    assert set(loaded.setlists.keys()) == {"Factory", "User"}
    assert len(loaded.setlists["Factory"]) == 4
    assert len(loaded.setlists["User"]) == 4
    assert loaded.setlists["User"][0]["meta"]["name"] == sample_preset["meta"]["name"]


def test_write_backup_requires_setlists(tmp_path: Path):
    """Attempting to write an empty backup with no setlists raises ValueError."""
    out_file = tmp_path / "empty.pgb"
    empty_backup = pgb.Backup(globals={}, setlists={})
    with pytest.raises(ValueError, match="at least one setlist"):
        pgb.write_backup(out_file, empty_backup)


def test_write_backup_with_irs(tmp_path: Path, sample_preset: dict):
    """IR binary streams in .pgb should be written and preserved without breaking read_backup."""
    out_file = tmp_path / "with_irs.pgb"
    mock_ir_wav = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00data\x00\x00\x00\x00"
    backup = pgb.Backup(
        globals={"System": {}},
        setlists={"User": [sample_preset]},
    )

    pgb.write_backup(out_file, backup, irs=[mock_ir_wav])
    loaded = pgb.read_backup(out_file)
    assert "User" in loaded.setlists
    assert len(loaded.setlists["User"]) == 1


def test_export_and_import_presets_zip_roundtrip(tmp_path: Path, sample_preset: dict):
    """Presets can be exported into a .zip archive of .pgp files and imported back."""
    zip_path = tmp_path / "presets_bundle.zip"
    presets_by_setlist = {
        "Factory": [sample_preset],
        "User": [sample_preset],
    }

    pgb.export_presets_zip(zip_path, presets_by_setlist)
    assert zip_path.exists()

    # Import back from zip
    imported = pgb.import_presets_zip(zip_path)
    assert "Factory" in imported
    assert "User" in imported
    assert len(imported["Factory"]) == 1
    assert len(imported["User"]) == 1
    assert imported["Factory"][0]["meta"]["name"] == sample_preset["meta"]["name"]


def test_import_presets_zip_invalid_file(tmp_path: Path):
    """Importing from a non-zip file raises ValueError."""
    corrupt_file = tmp_path / "bad.zip"
    corrupt_file.write_text("not a zip")
    with pytest.raises(ValueError, match="not a valid zip"):
        pgb.import_presets_zip(corrupt_file)
