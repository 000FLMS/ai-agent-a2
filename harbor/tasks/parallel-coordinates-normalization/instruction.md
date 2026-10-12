# parallel-coordinates-normalization

<!-- Copied from tasks/parallel-coordinates-normalization/task.json. This is the prompt the three fixed agents
     were given, so do NOT reword it: check-submission holds both your runs
     and this file to the descriptor's wording. Add what your verifier needs
     under the heading below instead. -->

Read systems.csv and create a parallel-coordinates plot with one polyline for each system. Use the axes in exactly this order: latency_ms, error_rate_pct, throughput_mbps, energy_wh. Normalize each metric independently across all eight systems using (value - column minimum) / (column maximum - column minimum); do not reverse any axis. Place ticks at 0, 0.5, and 1 on every normalized axis. Color lines consistently by cohort (Reference or Candidate), and include a legend for the cohorts. Label each vertical axis with its metric name and its original minimum and maximum values. Title the plot 'System Profiles (Column-wise Min-Max Scaling)'. Save the figure as figure.png.

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
3. **`/app/plotted_values.json`** - the normalized values shown in the chart.
   Write one JSON object with exactly three keys: `metrics`, an array of the
   four metric names in plot order; `ranges`, an object mapping each metric to
   a two-number `[minimum, maximum]` array; and `systems`, an array with one
   object per input row. Each system object has `name` and `cohort` strings and
   `normalized`, an array of four JSON numbers in metric order. For example,
   `{"metrics":["latency_ms"],"ranges":{"latency_ms":[0,1]},"systems":[{"name":"Example","cohort":"Reference","normalized":[0.0]}]}`
   illustrates the shape; include all four metrics and all eight systems in
   your output.

Do not modify `systems.csv`. Generate the sidecar from the same normalized
values used to draw the lines.

Only the libraries already installed are available and there is no network
access; everything you need is in the image.
