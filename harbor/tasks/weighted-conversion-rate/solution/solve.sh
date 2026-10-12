#!/bin/bash
# Reference solution.  The oracle agent (`-a oracle`) runs this in /app; it is
# what proves your task is solvable and that your verifier can say yes.
set -euo pipefail

APP_DIR="${HARBOR_APP_DIR:-/app}"

cat > "$APP_DIR/plot.py" <<'PY'
import csv
import json
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

totals = defaultdict(lambda: [0, 0])
with open("campaigns.csv", newline="") as handle:
    for row in csv.DictReader(handle):
        totals[row["channel"]][0] += int(row["conversions"])
        totals[row["channel"]][1] += int(row["visits"])
rates = [
    (channel, round(conversions / visits * 100, 1))
    for channel, (conversions, visits) in totals.items()
]
rates.sort(key=lambda item: item[1], reverse=True)
channels = [channel for channel, _ in rates]
values = [rate for _, rate in rates]

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.barh(channels[::-1], values[::-1], color="#2563eb")
ax.set_title("Overall Conversion Rate by Channel")
ax.set_xlabel("Conversion rate (%)")
ax.set_ylabel("Channel")
for bar, value in zip(bars, values[::-1]):
    ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}%", va="center")
ax.set_xlim(0, max(values) * 1.18)
fig.tight_layout()
fig.savefig("figure.png", dpi=120)

with open("plotted_values.json", "w") as handle:
    json.dump({"channels": channels, "conversion_rate_pct": values},
              handle, indent=2)
    handle.write("\n")
PY

cd "$APP_DIR"
python plot.py
