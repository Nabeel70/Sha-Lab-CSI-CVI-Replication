#!/usr/bin/env python3
"""
Step 4: Extract posture-change event times from .anI annotations.

The PRCP dataset labels events like 'Initiate slow tilt up' directly.
This is more reliable than guessing from the Angle channel alone.

Output: results/tables/<record>_posture_events.csv
        results/figures/<record>_posture_timeline.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import wfdb

from prcp_utils import find_prcp_dataset_dir, find_project_root, record_path

DEFAULT_RECORD = "12726"


def extract_posture_events(dataset_dir: Path, record_name: str) -> pd.DataFrame:
    path = record_path(dataset_dir, record_name)
    record = wfdb.rdrecord(path, physical=False)
    fs = record.fs

    ann = wfdb.rdann(path, "anI")
    times_s = np.asarray(ann.sample, dtype=float) / fs
    labels = [note.strip() for note in ann.aux_note]

    return pd.DataFrame(
        {
            "record_name": record_name,
            "event_index": np.arange(1, len(labels) + 1),
            "time_s": np.round(times_s, 3),
            "sample": ann.sample,
            "label": labels,
        }
    )


def plot_timeline(events: pd.DataFrame, fig_dir: Path) -> Path:
    record_name = events["record_name"].iloc[0]
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig_path = fig_dir / f"{record_name}_posture_timeline.png"

    fig, ax = plt.subplots(figsize=(14, max(4, 0.35 * len(events))))
    y_pos = np.arange(len(events))

    ax.hlines(y_pos, 0, events["time_s"], color="lightgray", linewidth=1)
    ax.plot(events["time_s"], y_pos, "o", color="tab:blue")

    for t, y, label in zip(events["time_s"], y_pos, events["label"]):
        ax.text(t + 5, y, label, va="center", fontsize=9)

    ax.set_xlabel("Time (s)")
    ax.set_yticks([])
    ax.set_title(f"{record_name}: posture events from .anI annotations")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract posture events from anI file.")
    parser.add_argument("--record", default=DEFAULT_RECORD)
    args = parser.parse_args()

    project_root = find_project_root()
    dataset_dir = find_prcp_dataset_dir(project_root)

    print(f"Dataset folder: {dataset_dir}")
    print(f"Extracting posture events for record: {args.record}")

    events = extract_posture_events(dataset_dir, args.record)

    table_dir = project_root / "results" / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    csv_path = table_dir / f"{args.record}_posture_events.csv"
    events.to_csv(csv_path, index=False)

    fig_path = plot_timeline(events, project_root / "results" / "figures")

    print(f"\nFound {len(events)} events:")
    for _, row in events.iterrows():
        print(f"  {row['time_s']:8.1f}s  {row['label']}")

    print(f"\nSaved event table: {csv_path}")
    print(f"Saved timeline plot: {fig_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
