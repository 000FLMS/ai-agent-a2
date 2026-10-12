# cumulative-net-sales

<!-- The descriptor prompt above is kept verbatim. Packaging requirements are
     added below so the original task stays unchanged. -->

Read transactions.csv, which contains transaction-level sales; negative amounts are refunds and must remain negative. First sum net sales by date and product, then sort dates chronologically and compute a separate cumulative sum over dates for each product. Plot one line per product using those cumulative totals. Label the axes 'Date' and 'Cumulative net sales ($)', include a legend, and title the chart 'Cumulative Net Sales by Product'. Save the figure as figure.png.

## Required outputs

Leave these behind in `/app`, which is also the working directory. In `plot.py`,
refer to `transactions.csv` and `figure.png` by bare filename rather than by
absolute path. The verifier re-runs the script in a copied workspace, so
absolute paths would point outside that copy.

Extra images are allowed. Save the required chart as `figure.png`.

1. **`/app/plot.py`** - the plotting script. Self-contained and re-runnable:
   `python plot.py` from `/app` must reproduce the figure with no arguments and
   no manual steps. It must read the input file rather than hard-code results,
   and it must render the same image every time it runs.
2. **`/app/figure.png`** - the chart, as saved by that script.
3. **`/app/plotted_values.json`** - the values shown in the chart, generated from the same variables used to draw it. 
   Write one JSON object with exactly two keys: `dates`, an array of ISO date strings in chronological order, and
   `series`, an object with exactly the product names as keys. Each product's value must be an array of JSON numbers aligned with `dates`; do not include currency symbols or formatted strings. For example, this shows the required
   shape with placeholder zero values:
   `{"dates": ["2025-02-01"], "series": {"Widget A": [0.0], "Widget B": [0.0]}}`.

Do not modify `transactions.csv`. The script must read the input file and produce the same outputs every time it runs.

Only the libraries already installed are available and there is no network access; everything you need is in the image.
