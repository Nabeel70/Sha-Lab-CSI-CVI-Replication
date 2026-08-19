# Results — what each file is

These files are from the Python **approximate** CSI/CVI pipeline on PhysioNet PRCP (tilt). Re-running the scripts overwrites them.

## Figures (`results/figures/`)

| File | What you should see |
|------|---------------------|
| `12726_channels.png` | First 5 min of raw ABP, ECG, table angle for subject 12726 |
| `12726_ibi.png` | Inter-beat intervals and instantaneous HR |
| `12726_posture_timeline.png` | Annotated posture events (including slow tilt up) |
| `12726_csi_cvi_full.png` | CSI (red) and CVI (green) over the whole recording |
| `12726_csi_cvi_initiate_slow_tilt_up.png` | **Main check:** time 0 = slow tilt; CSI should rise, CVI should fall |
| `group_csi_cvi_pre_post.png` | All 10 subjects: mean CSI/CVI before vs after slow tilt |

## Tables (`results/tables/`)

| File | What it is |
|------|------------|
| `prcp_inventory.csv` | 10 records: sampling rate, duration, channels, annotations |
| `*_posture_events.csv` | Event times/labels for each record |
| `12726_pre_post_summary.csv` | One-subject CSI/CVI mean pre vs post (±120 s around tilt) |
| `group_pre_post_summary.csv` | Same for all 10 records |
| `group_direction_check.csv` | **Headline result: 9/10 matched CSI↑ and CVI↓ (90%)** |

## Intermediate (`results/intermediate/`)

| File | What it is |
|------|------------|
| `*_ibi.npy` | Cleaned IBI (seconds) + times, used as CSI/CVI input |
| `*_csi_cvi.npz` | Time, CSI, CVI, and HR/HRV components at 4 Hz |

You can replot from these without reloading PhysioNet, or delete them and recompute from the dataset.
