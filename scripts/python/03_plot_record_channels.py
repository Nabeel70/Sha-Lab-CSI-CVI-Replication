#!/usr/bin/env python3
"""
Step 3: Plot ECG, arterial blood pressure (ABP), and table angle for one record.

Output: results/figures/<record>_channels.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import wfdb

from prcp_utils import find_prcp_dataset_dir, find_project_root, record_path

DEFAULT_RECORD = "12726"
PLOT_SECONDS = 300  # first 5 minutes


def plot_channels(dataset_dir: Path, record_name: str, plot_seconds: int, fig_dir: Path) -> Path:
    path = record_path(dataset_dir, record_name)
    record = wfdb.rdrecord(path)
    fs = record.fs
    n_samples = min(int(plot_seconds * fs), record.sig_len)

    time = np.arange(n_samples) / fs
    signals = record.p_signal[:n_samples, :]
    names = record.sig_name

    fig, axes = plt.subplots(len(names), 1, figsize=(12, 2.5 * len(names)), sharex=True)
    if len(names) == 1:
        axes = [axes]

    for ax, name, sig in zip(axes, names, signals.T):
        ax.plot(time, sig, linewidth=0.5)
        ax.set_ylabel(name)
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Time (s)")
    fig.suptitle(f"{record_name}: first {plot_seconds} seconds", y=1.01)
    fig.tight_layout()

    fig_dir.mkdir(parents=True, exist_ok=True)
    fig_path = fig_dir / f"{record_name}_channels.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot PRCP signal channels.")
    parser.add_argument("--record", default=DEFAULT_RECORD)
    parser.add_argument("--seconds", type=int, default=PLOT_SECONDS)
    args = parser.parse_args()

    project_root = find_project_root()
    dataset_dir = find_prcp_dataset_dir(project_root)

    print(f"Dataset folder: {dataset_dir}")
    print(f"Plotting record {args.record} for first {args.seconds} s")

    fig_path = plot_channels(
        dataset_dir, args.record, args.seconds, project_root / "results" / "figures"
    )
    print(f"Saved channel plot: {fig_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
