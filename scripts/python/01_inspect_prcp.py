#!/usr/bin/env python3
"""Inspect the local PhysioNet PRCP dataset and write an inventory CSV."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import wfdb


def find_project_root() -> Path:
    """Return the project root (directory containing this script's ancestor)."""
    return Path(__file__).resolve().parents[2]


def find_prcp_dataset_dir(project_root: Path) -> Path:
    """Locate the PRCP dataset folder by searching for RECORDS and .hea files."""
    records_files = sorted(project_root.rglob("RECORDS"))
    if not records_files:
        raise FileNotFoundError(
            f"No RECORDS file found under {project_root}. "
            "Ensure the PhysioNet PRCP dataset is downloaded."
        )

    candidates: list[Path] = []
    for records_file in records_files:
        dataset_dir = records_file.parent
        hea_files = list(dataset_dir.glob("*.hea"))
        if hea_files:
            candidates.append(dataset_dir)

    if not candidates:
        raise FileNotFoundError(
            f"Found RECORDS file(s) but no .hea files alongside them under {project_root}."
        )

    if len(candidates) > 1:
        print("Warning: multiple candidate PRCP folders found; using the first:")
        for candidate in candidates:
            print(f"  - {candidate}")

    return candidates[0]


def load_record_names(dataset_dir: Path) -> list[str]:
    """Read record names from RECORDS, falling back to .hea stems."""
    records_file = dataset_dir / "RECORDS"
    if records_file.exists():
        names = [
            line.strip()
            for line in records_file.read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if names:
            return names

    return sorted(path.stem for path in dataset_dir.glob("*.hea"))


def load_known_annotators(dataset_dir: Path) -> dict[str, str]:
    """Parse ANNOTATORS file into {extension: description}."""
    annotators_file = dataset_dir / "ANNOTATORS"
    if not annotators_file.exists():
        return {}

    known: dict[str, str] = {}
    for line in annotators_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        ext = parts[0]
        desc = parts[1] if len(parts) > 1 else ""
        known[ext] = desc
    return known


def find_available_annotations(record_name: str, dataset_dir: Path) -> list[str]:
    """Return annotation extensions present for a record (excluding hea/dat)."""
    skip_ext = {"hea", "dat"}
    extensions: set[str] = set()
    for path in dataset_dir.glob(f"{record_name}.*"):
        ext = path.suffix.lstrip(".")
        if ext and ext not in skip_ext:
            extensions.add(ext)
    return sorted(extensions)


def inspect_record(record_name: str, dataset_dir: Path) -> dict:
    """Load one WFDB record and collect inventory metadata."""
    record_path = str(dataset_dir / record_name)
    record = wfdb.rdrecord(record_path, physical=False)

    duration_s = record.sig_len / record.fs if record.fs else float("nan")
    annotation_types = find_available_annotations(record_name, dataset_dir)

    return {
        "record_name": record_name,
        "sample_rate_hz": record.fs,
        "n_samples": record.sig_len,
        "duration_s": round(duration_s, 3),
        "duration_min": round(duration_s / 60.0, 3),
        "n_channels": record.n_sig,
        "channel_names": ";".join(record.sig_name),
        "annotation_types": ";".join(annotation_types),
    }


def print_record_summary(row: dict, known_annotators: dict[str, str]) -> None:
    """Print a human-readable summary for one record."""
    print(f"\nRecord: {row['record_name']}")
    print(f"  Sample rate: {row['sample_rate_hz']} Hz")
    print(
        f"  Duration: {row['duration_s']} s "
        f"({row['duration_min']} min, {row['n_samples']} samples)"
    )
    print(f"  Channels ({row['n_channels']}): {row['channel_names'].replace(';', ', ')}")

    annot_types = row["annotation_types"].split(";") if row["annotation_types"] else []
    if annot_types:
        print("  Annotation types:")
        for ext in annot_types:
            desc = known_annotators.get(ext, "")
            if desc:
                print(f"    - {ext}: {desc}")
            else:
                print(f"    - {ext}")
    else:
        print("  Annotation types: none found")


def main() -> int:
    project_root = find_project_root()
    dataset_dir = find_prcp_dataset_dir(project_root)
    known_annotators = load_known_annotators(dataset_dir)
    record_names = load_record_names(dataset_dir)

    print(f"Project root: {project_root}")
    print(f"PRCP dataset folder: {dataset_dir}")
    print(f"Found {len(record_names)} record(s) in RECORDS")

    rows: list[dict] = []
    for record_name in record_names:
        hea_path = dataset_dir / f"{record_name}.hea"
        if not hea_path.exists():
            print(f"\nWarning: skipping {record_name} (missing {hea_path.name})")
            continue

        try:
            row = inspect_record(record_name, dataset_dir)
            rows.append(row)
            print_record_summary(row, known_annotators)
        except Exception as exc:
            print(f"\nError inspecting {record_name}: {exc}", file=sys.stderr)

    if not rows:
        print("No records could be inspected.", file=sys.stderr)
        return 1

    output_dir = project_root / "results" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "prcp_inventory.csv"

    inventory = pd.DataFrame(rows)
    inventory.to_csv(output_csv, index=False)

    print(f"\nSaved inventory table to: {output_csv}")
    print(f"Total records inventoried: {len(inventory)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
