# Candia-Rivera CSI / CVI — Python replication

This folder is a **standalone copy** of one project: replicate cardiac sympathetic (CSI) and parasympathetic (CVI) time series from heartbeat intervals, following Candia-Rivera et al. 2025.

It is **not** a neural network. It is **not** PINA-D. CSI/CVI are Poincaré-plot indices computed from inter-beat intervals (IBI).

Paper: https://doi.org/10.1098/rsos.240750  
Authors’ MATLAB: https://github.com/diegocandiar/robust_hrv  
In the paper the parasympathetic index is often **CPI**. In code it is **CVI**. Same quantity.

---

## Honest statement: is this 100% the MATLAB paper code?

**No.**

| What | Status |
|------|--------|
| Same idea (Poincaré CSI/CVI from IBI) | Yes |
| Same settings we used: 15 s window, 4 Hz output | Yes |
| Same formulas as MATLAB `method='approximate'` in `compute_rCSI_rCVI_type.m` | Yes — that is what `scripts/python/05_compute_csi_cvi_approx.py` implements |
| Paper’s main **robust** MATLAB method | **Not run** |
| Bit-for-bit match vs MATLAB on the same IBI file | **Not verified** |

Say this to lab members: we reimplemented the authors’ **approximate** CSI/CVI in Python, then checked tilt physiology (CSI↑ / CVI↓ after slow tilt-up in **9/10** subjects).

---

## Folder map (where is what)

```text
candia_rivera_csi_cvi_replication/
  README.md                 ← you are here
  CITATION.md               ← paper citation
  requirements.txt          ← Python packages
  .gitignore                ← do not commit the PhysioNet .dat files

  scripts/
    run_pipeline.sh         ← one-command demo (subject 12726)
    python/
      01_inspect_prcp.py             inventory
      02_extract_ibi_from_prcp.py    beats → IBI
      03_plot_record_channels.py     raw ECG / BP / angle
      04_extract_posture_events.py   tilt event times
      05_compute_csi_cvi_approx.py   ★ CSI / CVI function
      06_plot_csi_cvi_around_event.py  plot around tilt
      07_batch_all_records.py        all 10 subjects + 9/10 table
      prcp_utils.py                  finds the PRCP dataset folder

  external/robust_hrv/      ← authors’ original MATLAB (.m only)
    compute_rCSI_rCVI_type.m   ★ official function (approximate / robust / exact)

  data/
    README.md               ← download PhysioNet PRCP here (not in git)

  results/
    README.md               ← what each figure/table means
    figures/                ← plots (already filled from our run)
    tables/                 ← CSVs including 9/10 direction check
    intermediate/           ← IBI .npy and CSI/CVI .npz from our run
```

**Files you should open first**

1. `results/figures/12726_csi_cvi_initiate_slow_tilt_up.png` — dashed line = slow tilt; CSI (red) should go up, CVI (green) down  
2. `results/figures/group_csi_cvi_pre_post.png` — all 10 subjects  
3. `results/tables/group_direction_check.csv` — **9/10 (90%)** matched CSI↑ and CVI↓  

---

## What we did (pipeline)

```text
PhysioNet PRCP (ECG + beat annotations + posture labels)
        ↓  02
IBI (seconds between R-peaks)
        ↓  05  (Python approximate CSI/CVI)
CSI(t) and CVI(t) at 4 Hz
        ↓  06 / 07
Align to first "slow tilt up", compare mean CSI/CVI 120 s before vs after
```

Expected physiology after tilt-up: sympathetic-like **CSI increases**, parasympathetic-like **CVI decreases**.

Our group result (`results/tables/group_direction_check.csv`):

- 10 records  
- CSI up: 9  
- CVI down: 10  
- Both: **9 / 10 (90%)**  
- Mean CSI change ≈ +0.11; mean CVI change ≈ −0.26  
- Record `12821` did not match CSI-up (CSI slightly down; CVI still down)

---

## How to re-run (track / reproduce)

### 1. Install

```bash
cd candia_rivera_csi_cvi_replication
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Download data

Follow `data/README.md`. Unzip PRCP 1.0.0 under `data/` so a `RECORDS` file exists next to the `.hea` files.

### 3. One subject (same as our demo)

```bash
chmod +x scripts/run_pipeline.sh
./scripts/run_pipeline.sh 12726
```

This overwrites that subject’s files under `results/`.

### 4. All 10 subjects (same as our 9/10 table)

```bash
python3 scripts/python/07_batch_all_records.py
```

Writes:

- `results/tables/group_pre_post_summary.csv`  
- `results/tables/group_direction_check.csv`  
- `results/figures/group_csi_cvi_pre_post.png`  
- `results/intermediate/<id>_ibi.npy` and `<id>_csi_cvi.npz`

### 5. Optional MATLAB (authors’ code)

If you have MATLAB, add `external/robust_hrv/` to the path:

```matlab
out = compute_rCSI_rCVI_type(ibi, t_ibi, 15, 'approximate');  % matches our Python
out = compute_rCSI_rCVI_type(ibi, t_ibi, 15, 'robust');       % paper’s robust method (we did not run this)
```

`ibi` = interval lengths in seconds, `t_ibi` = time of each interval in seconds.

---

## How to upload this folder to GitHub (share only the link)

Do **not** upload the parent lab project. Upload **this folder only**.

1. Create an empty GitHub repository (no README).  
2. On your computer:

```bash
cd candia_rivera_csi_cvi_replication
git init
git add .
git commit -m "Add Python CSI/CVI approximate replication (Candia-Rivera 2025)."
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

Then send lab mates **only** that GitHub URL. They clone it, download PRCP, and run the commands above.

Do not commit the PhysioNet `.dat` files (`.gitignore` already excludes them).

---

## What this folder does **not** include

- PINA-D / neural-network training  
- Cold-pressor dataset  
- HCP / resting fMRI physiology files (do not email those)

Those are separate work. This folder is the **paper CSI/CVI replication** only.
