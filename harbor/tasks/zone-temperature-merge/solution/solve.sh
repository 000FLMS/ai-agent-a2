#!/bin/bash
# Reference solution.  The oracle agent (`-a oracle`) runs this in /app; it is
# what proves your task is solvable and that your verifier can say yes.
set -euo pipefail

APP_DIR="${HARBOR_APP_DIR:-/app}"

cat > "$APP_DIR/plot.py" <<'PY'
import csv
import json
from collections import defaultdict
from statistics import median

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

zones_by_sensor = {}
with open("sites.csv", newline="") as handle:
    for row in csv.DictReader(handle):
        zones_by_sensor[row["sensor_id"]] = row["zone"]

readings = defaultdict(list)
with open("readings.csv", newline="") as handle:
    for row in csv.DictReader(handle):
        if row["status"] == "valid" and row["temp_c"].strip():
            zone = zones_by_sensor[row["sensor_id"]]
            readings[(row["date"], zone)].append(float(row["temp_c"]))

dates = sorted({date for date, _ in readings})
zones = sorted({zone for _, zone in readings})
series = {
    zone: [median(readings[(date, zone)]) for date in dates]
    for zone in zones
}

fig, ax = plt.subplots(figsize=(7, 4))
for zone in zones:
    ax.plot(dates, series[zone], marker="o", label=zone)
ax.set_xlabel("Date")
ax.set_ylabel("Median temperature (C)")
ax.set_title("Daily Median Temperature by Zone")
ax.legend(title="Zone")
ax.grid(axis="y", alpha=0.25)
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig("figure.png", dpi=120)

with open("plotted_values.json", "w") as handle:
    json.dump({"dates": dates, "zones": series}, handle, indent=2)
    handle.write("\n")
PY

cd "$APP_DIR"
python plot.py
