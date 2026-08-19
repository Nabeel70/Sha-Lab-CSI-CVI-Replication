# Data (download, do not commit)

This replication uses the public PhysioNet dataset:

**Physiologic Response to Changes in Posture (PRCP) 1.0.0**  
https://physionet.org/content/prcp/1.0.0/

Unzip it **inside this `data/` folder** (or anywhere under the replication folder). Scripts search for a `RECORDS` file next to `.hea` records.

Example after unzip:

```text
data/physiologic-response-to-changes-in-posture-1.0.0/
  RECORDS
  12726.hea
  12726.dat
  12726.wqrs
  12726.anI
  ...
```

The WFDB files are **not** included in this GitHub folder (size + PhysioNet terms). Lab members download them once, then run the scripts.
