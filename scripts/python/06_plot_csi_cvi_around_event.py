#!/usr/bin/env python3
"""
Step 6: Plot CSI and CVI aligned to a posture-change event (-120 to +120 seconds).

Expected pattern after tilt/stand up:
  - CSI (sympathetic) increases
  - CVI (parasympathetic) decreases

Input:  results/intermediate/<record>_csi_cvi.npz
        results/tables/<record>_posture_events.csv
Output: results/figures/<record>_csi_cvi_<event_slug>.png
        results/tables/<record>_pre_post_summary.csv
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT_RECORD = "12726"
DEFAULT_EVENT_LABEL = "Initiate slow tilt up"
ALIGN_WINDOW_S = 120.0


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "event"


def load_event_time(events_csv: Path, event_label: str) -> tuple[float, str]:
    events = pd.read_csv(events_csv)
    match = events[events["label"] == event_label]
    if match.empty:
        available = "\n".join(f"  - {label}" for label in events["label"])
        raise ValueError(
            f"Event '{event_label}' not found.\nAvailable events:\n{available}"
        )
    row = match.iloc[0]
    return float(row["time_s"]), str(row["label"])


def summarize_pre_post(
    aligned_time: np.ndarray,
    csi: np.ndarray,
    cvi: np.ndarray,
    record_name: str,
    event_label: str,
    event_time_s: float,
) -> pd.DataFrame:
    pre = aligned_time < 0
    post = aligned_time >= 0

    return pd.DataFrame(
        [
            {
                "record_name": record_name,
                "event_label": event_label,
                "event_time_s": event_time_s,
                "window": "pre",
                "CSI_mean": float(np.mean(csi[pre])),
                "CVI_mean": float(np.mean(cvi[pre])),
                "n_samples": int(pre.sum()),
            },
            {
                "record_name": record_name,
                "event_label": event_label,
                "event_time_s": event_time_s,
                "window": "post",
                "CSI_mean": float(np.mean(csi[post])),
                "CVI_mean": float(np.mean(cvi[post])),
                "n_samples": int(post.sum()),
            },
        ]
    )


def plot_aligned(
    aligned_time: np.ndarray,
    csi: np.ndarray,
    cvi: np.ndarray,
    record_name: str,
    event_label: str,
    fig_dir: Path,
) -> Path:
    fig_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(event_label)
    fig_path = fig_dir / f"{record_name}_csi_cvi_{slug}.png"

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)

    axes[0].plot(aligned_time, csi, color="tab:red", linewidth=1.2)
    axes[0].axvline(0, color="black", linestyle="--", linewidth=1, label="posture onset")
    axes[0].set_ylabel("CSI")
    axes[0].set_title(f"{record_name}: CSI around '{event_label}'")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].plot(aligned_time, cvi, color="tab:green", linewidth=1.2)
    axes[1].axvline(0, color="black", linestyle="--", linewidth=1)
    axes[1].set_ylabel("CVI")
    axes[1].set_xlabel("Time relative to event (s)")
    axes[1].set_title("CVI around posture change")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)
    return fig_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot CSI/CVI around a posture event.")
    parser.add_argument("--record", default=DEFAULT_RECORD)
    parser.add_argument("--event", default=DEFAULT_EVENT_LABEL)
    parser.add_argument("--window", type=float, default=ALIGN_WINDOW_S)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    csi_file = project_root / "results" / "intermediate" / f"{args.record}_csi_cvi.npz"
    events_file = project_root / "results" / "tables" / f"{args.record}_posture_events.csv"

    if not csi_file.exists():
        raise FileNotFoundError(f"Missing {csi_file}. Run 05_compute_csi_cvi_approx.py first.")
    if not events_file.exists():
        raise FileNotFoundError(f"Missing {events_file}. Run 04_extract_posture_events.py first.")

    data = np.load(csi_file)
    time_s = data["time"]
    csi = data["CSI"]
    cvi = data["CVI"]

    event_time_s, event_label = load_event_time(events_file, args.event)
    aligned_time = time_s - event_time_s

    mask = (aligned_time >= -args.window) & (aligned_time <= args.window)
    aligned_time = aligned_time[mask]
    csi = csi[mask]
    cvi = cvi[mask]

    summary = summarize_pre_post(
        aligned_time, csi, cvi, args.record, event_label, event_time_s
    )

    table_dir = project_root / "results" / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    summary_path = table_dir / f"{args.record}_pre_post_summary.csv"
    summary.to_csv(summary_path, index=False)

    fig_path = plot_aligned(
        aligned_time,
        csi,
        cvi,
        args.record,
        event_label,
        project_root / "results" / "figures",
    )

    pre = summary[summary["window"] == "pre"].iloc[0]
    post = summary[summary["window"] == "post"].iloc[0]

    print(f"Aligned to event: '{event_label}' at t={event_time_s:.1f}s")
    print(f"Window: -{args.window:.0f} to +{args.window:.0f} seconds")
    print("\nPre vs post means:")
    print(f"  CSI: pre={pre['CSI_mean']:.3f}  post={post['CSI_mean']:.3f}  "
          f"change={post['CSI_mean'] - pre['CSI_mean']:+.3f}")
    print(f"  CVI: pre={pre['CVI_mean']:.3f}  post={post['CVI_mean']:.3f}  "
          f"change={post['CVI_mean'] - pre['CVI_mean']:+.3f}")

    csi_up = post["CSI_mean"] > pre["CSI_mean"]
    cvi_down = post["CVI_mean"] < pre["CVI_mean"]
    if csi_up and cvi_down:
        print("\nSanity check: matches paper expectation (CSI up, CVI down).")
    else:
        print("\nSanity check: pattern does NOT fully match expectation yet.")
        print("This can happen with approximate method or wrong event choice.")
        print("Try another event label or inspect the full trace plot.")

    print(f"\nSaved aligned plot:   {fig_path}")
    print(f"Saved pre/post table: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
