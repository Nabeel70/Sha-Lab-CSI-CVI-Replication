#!/usr/bin/env python3
"""
Step 2: Extract inter-beat intervals (IBI) from PRCP .wqrs annotations.

Input:  physiologic-response-to-changes-in-posture-1.0.0/<record>.wqrs
Output: results/intermediate/<record>_ibi.npy
        results/figures/<record>_ibi.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import wfdb

from prcp_utils import find_prcp_dataset_dir, find_project_root, record_path

DEFAULT_RECORD = "12726"
IBI_MIN_S = 0.3
IBI_MAX_S = 2.0


def extract_ibi(dataset_dir: Path, record_name: str) -> dict:
    path = record_path(dataset_dir, record_name)
    record = wfdb.rdrecord(path)
    fs = record.fs

    ann = wfdb.rdann(path, "wqrs")
    r_samples = np.asarray(ann.sample, dtype=float)
    r_times = r_samples / fs

    ibi = np.diff(r_times)
    t_ibi = r_times[1:]

    mask = (ibi > IBI_MIN_S) & (ibi < IBI_MAX_S)
    ibi_clean = ibi[mask]
    t_ibi_clean = t_ibi[mask]

    return {
        "record_name": record_name,
        "fs": fs,
        "r_times": r_times,
        "ibi": ibi_clean,
        "t_ibi": t_ibi_clean,
        "n_beats_raw": len(r_times),
        "n_ibi_raw": len(ibi),
        "n_ibi_clean": len(ibi_clean),
    }


def save_ibi(data: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{data['record_name']}_ibi.npy"
    np.save(
        out_file,
        {
            "ibi": data["ibi"],
            "t_ibi": data["t_ibi"],
            "record_name": data["record_name"],
            "fs": data["fs"],
        },
        allow_pickle=True,
    )
    return out_file


def plot_ibi(data: dict, fig_dir: Path) -> Path:
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig_path = fig_dir / f"{data['record_name']}_ibi.png"

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=False)

    axes[0].plot(data["t_ibi"], data["ibi"], linewidth=0.6, color="tab:blue")
    axes[0].set_ylabel("IBI (s)")
    axes[0].set_title(f"{data['record_name']}: inter-beat intervals (cleaned)")
    axes[0].grid(True, alpha=0.3)

    hr_bpm = 60.0 / data["ibi"]
    axes[1].plot(data["t_ibi"], hr_bpm, linewidth=0.6, color="tab:red")
    axes[1].set_ylabel("HR (bpm)")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_title("Instantaneous heart rate from IBI")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)
    return fig_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract IBI from PRCP wqrs annotations.")
    parser.add_argument("--record", default=DEFAULT_RECORD, help="Record name, e.g. 12726")
    args = parser.parse_args()

    project_root = find_project_root()
    dataset_dir = find_prcp_dataset_dir(project_root)

    print(f"Dataset folder: {dataset_dir}")
    print(f"Processing record: {args.record}")

    data = extract_ibi(dataset_dir, args.record)

    print(f"  R-peaks found:        {data['n_beats_raw']}")
    print(f"  IBI before cleaning:  {data['n_ibi_raw']}")
    print(f"  IBI after cleaning:   {data['n_ibi_clean']}")
    print(f"  Median IBI:           {np.median(data['ibi']):.3f} s")
    print(f"  Median HR:            {60.0 / np.median(data['ibi']):.1f} bpm")

    ibi_file = save_ibi(data, project_root / "results" / "intermediate")
    fig_file = plot_ibi(data, project_root / "results" / "figures")

    print(f"\nSaved IBI data:  {ibi_file}")
    print(f"Saved IBI plot:  {fig_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
