"""Shared helpers for loading the local PhysioNet PRCP dataset."""

from __future__ import annotations

from pathlib import Path


def find_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_prcp_dataset_dir(project_root: Path | None = None) -> Path:
    root = project_root or find_project_root()
    records_files = sorted(root.rglob("RECORDS"))
    if not records_files:
        raise FileNotFoundError(f"No RECORDS file found under {root}.")

    for records_file in records_files:
        dataset_dir = records_file.parent
        if list(dataset_dir.glob("*.hea")):
            return dataset_dir

    raise FileNotFoundError(f"Found RECORDS but no .hea files under {root}.")


def load_record_names(dataset_dir: Path) -> list[str]:
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


def record_path(dataset_dir: Path, record_name: str) -> str:
    return str(dataset_dir / record_name)
