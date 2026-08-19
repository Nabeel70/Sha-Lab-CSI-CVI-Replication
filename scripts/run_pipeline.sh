#!/usr/bin/env bash
# Run the full PRCP CSI/CVI pipeline for one record (default: 12726).
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RECORD="${1:-12726}"
PYTHON="${PYTHON:-python3}"

export MPLCONFIGDIR="${PROJECT_ROOT}/.matplotlib"
export MPLBACKEND="${MPLBACKEND:-Agg}"
mkdir -p "${MPLCONFIGDIR}"

SCRIPTS="${PROJECT_ROOT}/scripts/python"

echo "=== PRCP CSI/CVI pipeline for record ${RECORD} ==="
echo "Folder: ${PROJECT_ROOT}"
echo "Python: ${PYTHON}"

"${PYTHON}" "${SCRIPTS}/01_inspect_prcp.py"
"${PYTHON}" "${SCRIPTS}/02_extract_ibi_from_prcp.py" --record "${RECORD}"
"${PYTHON}" "${SCRIPTS}/03_plot_record_channels.py" --record "${RECORD}"
"${PYTHON}" "${SCRIPTS}/04_extract_posture_events.py" --record "${RECORD}"
"${PYTHON}" "${SCRIPTS}/05_compute_csi_cvi_approx.py" --record "${RECORD}"
"${PYTHON}" "${SCRIPTS}/06_plot_csi_cvi_around_event.py" --record "${RECORD}"

echo ""
echo "=== Done. Open: ==="
echo "  results/figures/${RECORD}_channels.png"
echo "  results/figures/${RECORD}_ibi.png"
echo "  results/figures/${RECORD}_posture_timeline.png"
echo "  results/figures/${RECORD}_csi_cvi_full.png"
echo "  results/figures/${RECORD}_csi_cvi_initiate_slow_tilt_up.png"
