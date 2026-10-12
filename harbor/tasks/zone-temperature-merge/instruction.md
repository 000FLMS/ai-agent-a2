# zone-temperature-merge

<!-- Copied from tasks/zone-temperature-merge/task.json. This is the prompt the three fixed agents
     were given, so do NOT reword it: check-submission holds both your runs
     and this file to the descriptor's wording. Add what your verifier needs
     under the heading below instead. -->

Use sites.csv to map each sensor_id to a zone, then use readings.csv to make a line chart of the daily median temperature for each zone. Include only rows whose status is 'valid' and whose temp_c value is present. A blank temperature is missing data, not zero. Group all valid sensor readings by date and zone before taking the median. Show dates in chronological order, label the axes 'Date' and 'Median temperature (C)', include a legend for the zones, and title the chart 'Daily Median Temperature by Zone'. Save the figure as figure.png.

## Required outputs

Leave these behind in `/app`, which is also the working directory. `plot.py` must
refer to these files by bare filename rather than by absolute path. State this
requirement explicitly: the verifier re-runs the script in a copied workspace,
so an absolute output path would point outside that copy.

Extra images are allowed; the required chart must be named `figure.png`.

1. **`/app/plot.py`** - the plotting script. Self-contained and re-runnable:
   `python plot.py` from `/app` must reproduce the figure with no arguments and
   no manual steps. It must read the input file rather than hard-code results,
   and it must render the same image every time it runs.
2. **`/app/figure.png`** - the chart, as saved by that script.
3. **`/app/plotted_values.json`** - the daily zone medians shown in the chart.
   Write one JSON object with exactly two keys: `dates`, an array of ISO date
   strings in chronological order, and `zones`, an object mapping each zone
   name to an equally sized array of JSON numbers. For example,
   `{"dates":["2025-01-01"],"zones":{"North":[5.0],"South":[9.0]}}`.

Do not modify `sites.csv` or `readings.csv`. Generate the sidecar from the
same joined and grouped values used to draw the lines.

Only the libraries already installed are available and there is no network
access; everything you need is in the image.
