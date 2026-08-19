#!/usr/bin/env python3
"""
Step 7: Run the full pipeline on ALL PRCP records and summarize pre/post CSI/CVI.

For each record:
  - extract IBI
  - extract posture events
  - compute approximate CSI/CVI
  - summarize around the FIRST 'Initiate slow tilt up' event

Outputs:
  results/tables/group_pre_post_summary.csv
  results/tables/group_direction_check.csv
  results/figures/group_csi_cvi_pre_post.png
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Allow importing sibling scripts as modules
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from prcp_utils import find_prcp_dataset_dir, find_project_root, load_record_names  # noqa: E402


def load_module(name: str, filename: str):
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SLOW_TILT_UP_PATTERNS = (
    "initiate slow tilt up",
    "initiation of slow tilt up",
    "start slow tilt up",
)


def first_slow_tilt_up(events: pd.DataFrame) -> tuple[float, str] | None:
    """Find first slow-tilt-up event. Labels vary slightly across records."""
    labels_lower = events["label"].str.lower().str.strip()
    for pattern in SLOW_TILT_UP_PATTERNS:
        match = events[labels_lower == pattern]
        if not match.empty:
            row = match.iloc[0]
            return float(row["time_s"]), str(row["label"])
    # Fuzzy fallback: contains both "slow" and "tilt up" / "tiltup"
    fuzzy = events[
        labels_lower.str.contains("slow", na=False)
        & labels_lower.str.contains("tilt", na=False)
        & labels_lower.str.contains("up", na=False)
        & ~labels_lower.str.contains("down", na=False)
        & ~labels_lower.str.contains("end", na=False)
        & ~labels_lower.str.contains("conclude", na=False)
        & ~labels_lower.str.contains("conclusion", na=False)
    ]
    if not fuzzy.empty:
        row = fuzzy.iloc[0]
        return float(row["time_s"]), str(row["label"])
    return None


def main() -> int:
    extract_ibi = load_module("extract_ibi", "02_extract_ibi_from_prcp.py")
    extract_events = load_module("extract_events", "04_extract_posture_events.py")
    compute_csi = load_module("compute_csi", "05_compute_csi_cvi_approx.py")

    project_root = find_project_root()
    dataset_dir = find_prcp_dataset_dir(project_root)
    records = load_record_names(dataset_dir)

    intermediate = project_root / "results" / "intermediate"
    tables = project_root / "results" / "tables"
    figures = project_root / "results" / "figures"
    intermediate.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    print(f"Dataset: {dataset_dir}")
    print(f"Records: {len(records)}")

    rows: list[dict] = []

    for record_name in records:
        print(f"\n=== {record_name} ===")
        try:
            ibi_data = extract_ibi.extract_ibi(dataset_dir, record_name)
            extract_ibi.save_ibi(ibi_data, intermediate)

            events = extract_events.extract_posture_events(dataset_dir, record_name)
            events.to_csv(tables / f"{record_name}_posture_events.csv", index=False)

            event = first_slow_tilt_up(events)
            if event is None:
                print("  SKIP: no slow-tilt-up event found")
                continue
            t0, event_label = event

            result = compute_csi.compute_csi_cvi_approx(ibi_data["ibi"], ibi_data["t_ibi"])
            np.savez(intermediate / f"{record_name}_csi_cvi.npz", **result)

            aligned = result["time"] - t0
            mask = (aligned >= -120.0) & (aligned <= 120.0)
            csi = result["CSI"][mask]
            cvi = result["CVI"][mask]
            aligned = aligned[mask]

            pre = aligned < 0
            post = aligned >= 0
            if pre.sum() < 10 or post.sum() < 10:
                print("  SKIP: not enough samples around event")
                continue

            csi_pre = float(np.mean(csi[pre]))
            csi_post = float(np.mean(csi[post]))
            cvi_pre = float(np.mean(cvi[pre]))
            cvi_post = float(np.mean(cvi[post]))

            row = {
                "record_name": record_name,
                "event_label": event_label,
                "event_time_s": t0,
                "n_ibi": ibi_data["n_ibi_clean"],
                "median_ibi_s": float(np.median(ibi_data["ibi"])),
                "CSI_pre": csi_pre,
                "CSI_post": csi_post,
                "CSI_change": csi_post - csi_pre,
                "CVI_pre": cvi_pre,
                "CVI_post": cvi_post,
                "CVI_change": cvi_post - cvi_pre,
                "CSI_up": csi_post > csi_pre,
                "CVI_down": cvi_post < cvi_pre,
                "matches_expectation": (csi_post > csi_pre) and (cvi_post < cvi_pre),
            }
            rows.append(row)

            print(
                f"  CSI {csi_pre:.3f} → {csi_post:.3f} ({row['CSI_change']:+.3f}) | "
                f"CVI {cvi_pre:.3f} → {cvi_post:.3f} ({row['CVI_change']:+.3f}) | "
                f"OK={row['matches_expectation']}"
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")

    if not rows:
        print("No records summarized.")
        return 1

    summary = pd.DataFrame(rows)
    summary_path = tables / "group_pre_post_summary.csv"
    summary.to_csv(summary_path, index=False)

    n = len(summary)
    n_ok = int(summary["matches_expectation"].sum())
    direction = pd.DataFrame(
        [
            {
                "n_records": n,
                "n_csi_up": int(summary["CSI_up"].sum()),
                "n_cvi_down": int(summary["CVI_down"].sum()),
                "n_both_match_expectation": n_ok,
                "pct_match": round(100.0 * n_ok / n, 1),
                "mean_CSI_change": float(summary["CSI_change"].mean()),
                "mean_CVI_change": float(summary["CVI_change"].mean()),
            }
        ]
    )
    direction_path = tables / "group_direction_check.csv"
    direction.to_csv(direction_path, index=False)

    # Group bar plot: pre vs post means
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    x = np.arange(n)
    width = 0.35

    axes[0].bar(x - width / 2, summary["CSI_pre"], width, label="pre", color="lightcoral")
    axes[0].bar(x + width / 2, summary["CSI_post"], width, label="post", color="tab:red")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(summary["record_name"], rotation=45, ha="right")
    axes[0].set_ylabel("CSI mean")
    axes[0].set_title("CSI pre vs post (slow tilt up)")
    axes[0].legend()
    axes[0].grid(True, axis="y", alpha=0.3)

    axes[1].bar(x - width / 2, summary["CVI_pre"], width, label="pre", color="lightgreen")
    axes[1].bar(x + width / 2, summary["CVI_post"], width, label="post", color="tab:green")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(summary["record_name"], rotation=45, ha="right")
    axes[1].set_ylabel("CVI mean")
    axes[1].set_title("CVI pre vs post (slow tilt up)")
    axes[1].legend()
    axes[1].grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    fig_path = figures / "group_csi_cvi_pre_post.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print("\n=== GROUP SUMMARY ===")
    print(direction.to_string(index=False))
    print(f"\nSaved: {summary_path}")
    print(f"Saved: {direction_path}")
    print(f"Saved: {fig_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
