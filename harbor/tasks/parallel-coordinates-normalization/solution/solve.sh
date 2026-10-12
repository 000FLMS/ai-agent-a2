#!/bin/bash
# Reference solution.  The oracle agent (`-a oracle`) runs this in /app; it is
# what proves your task is solvable and that your verifier can say yes.
set -euo pipefail

APP_DIR="${HARBOR_APP_DIR:-/app}"

cat > "$APP_DIR/plot.py" <<'PY'
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

metrics = ["latency_ms", "error_rate_pct", "throughput_mbps", "energy_wh"]
systems = []
with open("systems.csv", newline="") as handle:
    systems = list(csv.DictReader(handle))
ranges = {
    metric: [min(float(row[metric]) for row in systems),
             max(float(row[metric]) for row in systems)]
    for metric in metrics
}
plotted = []
for row in systems:
    normalized = [
        (float(row[metric]) - ranges[metric][0]) /
        (ranges[metric][1] - ranges[metric][0])
        for metric in metrics
    ]
    plotted.append({"name": row["system"], "cohort": row["cohort"],
                    "normalized": normalized})

colors = {"Reference": "#2563eb", "Candidate": "#dc2626"}
fig, ax = plt.subplots(figsize=(9, 5))
positions = range(len(metrics))
for system in plotted:
    ax.plot(positions, system["normalized"], marker="o", linewidth=1.8,
            color=colors[system["cohort"]], alpha=0.8)
labels = [f"{metric}\n({ranges[metric][0]:g}–{ranges[metric][1]:g})"
          for metric in metrics]
ax.set_xticks(list(positions), labels)
ax.set_yticks([0, 0.5, 1])
ax.set_ylim(-0.05, 1.05)
ax.set_ylabel("Normalized value")
ax.set_title("System Profiles (Column-wise Min-Max Scaling)")
ax.grid(axis="y", alpha=0.25)
legend = [Line2D([0], [0], color=colors[name], lw=2, label=name)
          for name in ("Reference", "Candidate")]
ax.legend(handles=legend, title="Cohort")
fig.tight_layout()
fig.savefig("figure.png", dpi=120)

with open("plotted_values.json", "w") as handle:
    json.dump({"metrics": metrics, "ranges": ranges, "systems": plotted},
              handle, indent=2)
    handle.write("\n")
PY

cd "$APP_DIR"
python plot.py
