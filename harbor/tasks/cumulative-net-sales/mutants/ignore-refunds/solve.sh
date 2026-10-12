#!/bin/bash
set -euo pipefail
APP_DIR="${HARBOR_APP_DIR:-/app}"

cat > "$APP_DIR/plot.py" <<'PY'
import csv
import json
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

daily = defaultdict(float)
with open("transactions.csv", newline="") as handle:
    for row in csv.DictReader(handle):
        # Treat refunds as zero instead of subtracting them.
        amount = max(float(row["amount"]), 0.0)
        daily[(row["date"], row["product"])] += amount

dates = sorted({date for date, _ in daily})
products = sorted({product for _, product in daily})
series = {}
for product in products:
    running_total = 0.0
    values = []
    for date in dates:
        running_total += daily.get((date, product), 0.0)
        values.append(running_total)
    series[product] = values

fig, ax = plt.subplots(figsize=(7, 4))
for product in products:
    ax.plot(dates, series[product], marker="o", label=product)
ax.set_xlabel("Date")
ax.set_ylabel("Cumulative net sales ($)")
ax.set_title("Cumulative Net Sales by Product")
ax.legend(title="Product")
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig("figure.png", dpi=100)
with open("plotted_values.json", "w") as handle:
    json.dump({"dates": dates, "series": series}, handle, indent=2)
    handle.write("\n")
PY

cd "$APP_DIR"
python plot.py
