#!/bin/bash
# Reference solution.  The oracle agent (`-a oracle`) runs this in /app; it is
# what proves your task is solvable and that your verifier can say yes.
set -euo pipefail

APP_DIR="${HARBOR_APP_DIR:-/app}"

cat > "$APP_DIR/plot.py" <<'PY'
import csv
import json
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

counts = {}
with open("incidents.csv", newline="") as handle:
    for row in csv.DictReader(handle):
        counts[row["date"]] = int(row["incident_count"])

weeks = [[None for _ in range(7)] for _ in range(5)]
first_weekday = date(2025, 2, 1).weekday()
for date_text, count in counts.items():
    day = date.fromisoformat(date_text)
    if day.year == 2025 and day.month == 2:
        offset = first_weekday + day.day - 1
        weeks[offset // 7][offset % 7] = count

values = np.array([
    [np.nan if value is None else value for value in week]
    for week in weeks
], dtype=float)
cmap = plt.get_cmap("Blues").copy()
cmap.set_bad("white")
fig, ax = plt.subplots(figsize=(9, 4.5))
image = ax.imshow(np.ma.masked_invalid(values), cmap=cmap, aspect="auto", vmin=0)
ax.set_xticks(range(7), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
ax.set_yticks(range(5), [f"Week {n}" for n in range(1, 6)])
ax.set_xticks(np.arange(-0.5, 7, 1), minor=True)
ax.set_yticks(np.arange(-0.5, 5, 1), minor=True)
ax.grid(which="minor", color="white", linewidth=2)
ax.tick_params(which="minor", bottom=False, left=False)
for row, week in enumerate(weeks):
    for column, count in enumerate(week):
        if count is not None:
            color = "white" if values[row, column] >= 5 else "black"
            ax.text(column, row, str(count), ha="center", va="center", color=color)
ax.set_title("Daily Incidents, February 2025")
colorbar = fig.colorbar(image, ax=ax)
colorbar.set_label("Incidents")
fig.tight_layout()
fig.savefig("figure.png", dpi=120)

with open("plotted_values.json", "w") as handle:
    json.dump({"weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
               "weeks": weeks}, handle, indent=2)
    handle.write("\n")
PY

cd "$APP_DIR"
python plot.py
