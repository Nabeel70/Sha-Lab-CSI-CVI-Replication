#!/usr/bin/env python3
"""
Step 5: Compute CSI and CVI using a Python reimplementation of the paper's
APPROXIMATE method (from external/robust_hrv/compute_rCSI_rCVI_type.m).

This is NOT the official MATLAB code. It follows the same formulas so you can
see results without installing MATLAB. For exact/robust replication, use the
MATLAB functions later.

Input:  results/intermediate/<record>_ibi.npy
Output: results/intermediate/<record>_csi_cvi.npz
        results/figures/<record>_csi_cvi_full.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d

DEFAULT_RECORD = "12726"
WINDOW_S = 15.0
OUTPUT_FS = 4.0  # Hz, matches MATLAB code


def flipsig(sig: np.ndarray) -> np.ndarray:
    """Mirror signal around its mean (same as MATLAB flipsig)."""
    msig = np.mean(sig)
    return -(sig - msig) + msig


def poincare_measures_approx(ibi: np.ndarray) -> tuple[float, float, float]:
    """Return SD1, SD2, D for the approximate Poincare method."""
    ibi = np.asarray(ibi, dtype=float)
    ibi1 = ibi[:-1]
    ibi2 = ibi[1:]
    sd = np.diff(ibi)

    sd1 = np.sqrt(0.5 * np.std(sd, ddof=1) ** 2)
    sd2 = np.sqrt(2 * (np.std(ibi, ddof=1) ** 2) - (0.5 * np.std(sd, ddof=1) ** 2))
    d0 = np.sqrt(np.mean(ibi1) ** 2 + np.mean(ibi2) ** 2)
    return sd1, sd2, d0


def compute_csi_cvi_approx(
    ibi: np.ndarray,
    t_ibi: np.ndarray,
    window_s: float = WINDOW_S,
    output_fs: float = OUTPUT_FS,
) -> dict:
    """
    Python port of compute_rCSI_rCVI_type(..., method='approximate').
    """
    ibi = np.asarray(ibi, dtype=float).ravel()
    t_ibi = np.asarray(t_ibi, dtype=float).ravel()

    sd01, sd02, d0 = poincare_measures_approx(ibi)

    # Find sliding-window end indices (same logic as MATLAB ixs = find(t_ibi > t2))
    t2_start = t_ibi[0] + window_s
    ixs = np.where(t_ibi > t2_start)[0]
    nt = len(ixs) - 1
    if nt < 2:
        raise ValueError("Not enough IBI samples for the chosen window length.")

    sd1 = np.zeros(nt)
    sd2 = np.zeros(nt)
    d_vals = np.zeros(nt)
    t_centers = np.zeros(nt)

    for k in range(nt):
        i = ixs[k]
        t2 = t_ibi[i]
        t1 = t_ibi[i] - window_s
        ix = np.where((t_ibi >= t1) & (t_ibi <= t2))[0]

        ibi_win = ibi[ix]
        ibi1 = ibi_win[:-1]
        ibi2 = ibi_win[1:]
        sd = np.diff(ibi_win)

        sd1[k] = np.sqrt(0.5 * np.std(sd, ddof=1) ** 2)
        sd2[k] = np.sqrt(2 * (np.std(ibi_win, ddof=1) ** 2) - (0.5 * np.std(sd, ddof=1) ** 2))
        d_vals[k] = np.sqrt(np.mean(ibi1) ** 2 + np.mean(ibi2) ** 2)
        t_centers[k] = np.median(t_ibi[ix])

    sd1 = sd1 - np.mean(sd1) + sd01
    sd2 = sd2 - np.mean(sd2) + sd02
    d_vals = d_vals - np.mean(d_vals) + d0

    cvi = sd1 * 10.0 + 1.0
    csi = sd2 * 1.0 + 1.0

    t_out = np.arange(t_centers[0], t_centers[-1], 1.0 / output_fs)
    interp_kind = "cubic" if len(t_centers) >= 4 else "linear"

    cvi_out = interp1d(t_centers, cvi, kind=interp_kind, fill_value="extrapolate")(t_out)
    csi_out = interp1d(t_centers, csi, kind=interp_kind, fill_value="extrapolate")(t_out)
    dv_out = interp1d(t_centers, d_vals, kind=interp_kind, fill_value="extrapolate")(t_out)
    ds_out = flipsig(dv_out)

    rcsi = ds_out + csi_out
    rcvi = dv_out + cvi_out

    return {
        "time": t_out,
        "CSI": rcsi,
        "CVI": rcvi,
        "CSI_HR": ds_out,
        "CVI_HR": dv_out,
        "CSI_HRV": csi_out,
        "CVI_HRV": cvi_out,
        "fsample": output_fs,
        "method": "approximate_python",
        "window_s": window_s,
    }


def plot_full_trace(result: dict, record_name: str, fig_dir: Path) -> Path:
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig_path = fig_dir / f"{record_name}_csi_cvi_full.png"

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    axes[0].plot(result["time"], result["CSI"], color="tab:red", linewidth=0.8)
    axes[0].set_ylabel("CSI")
    axes[0].set_title(f"{record_name}: cardiac sympathetic index (approximate)")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(result["time"], result["CVI"], color="tab:green", linewidth=0.8)
    axes[1].set_ylabel("CVI")
    axes[1].set_xlabel("Time (s)")
    axes[1].set_title("Cardiac parasympathetic / vagal index (approximate)")
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)
    return fig_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute approximate CSI/CVI in Python.")
    parser.add_argument("--record", default=DEFAULT_RECORD)
    parser.add_argument("--window", type=float, default=WINDOW_S)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[2]
    ibi_file = project_root / "results" / "intermediate" / f"{args.record}_ibi.npy"
    if not ibi_file.exists():
        raise FileNotFoundError(
            f"Missing {ibi_file}. Run 02_extract_ibi_from_prcp.py first."
        )

    payload = np.load(ibi_file, allow_pickle=True).item()
    ibi = payload["ibi"]
    t_ibi = payload["t_ibi"]

    print(f"Loaded IBI: {len(ibi)} intervals from {ibi_file.name}")
    print(f"Computing CSI/CVI with window={args.window}s (approximate Python method)")

    result = compute_csi_cvi_approx(ibi, t_ibi, window_s=args.window)

    out_dir = project_root / "results" / "intermediate"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{args.record}_csi_cvi.npz"
    np.savez(out_file, **result)

    fig_file = plot_full_trace(result, args.record, project_root / "results" / "figures")

    print(f"  Output time points: {len(result['time'])}")
    print(f"  CSI range: [{result['CSI'].min():.3f}, {result['CSI'].max():.3f}]")
    print(f"  CVI range: [{result['CVI'].min():.3f}, {result['CVI'].max():.3f}]")
    print(f"\nSaved CSI/CVI data: {out_file}")
    print(f"Saved CSI/CVI plot: {fig_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
