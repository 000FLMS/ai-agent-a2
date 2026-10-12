# weighted-conversion-rate

<!-- Copied from tasks/weighted-conversion-rate/task.json. This is the prompt the three fixed agents
     were given, so do NOT reword it: check-submission holds both your runs
     and this file to the descriptor's wording. Add what your verifier needs
     under the heading below instead. -->

Read campaigns.csv and make a horizontal bar chart of the conversion rate for each channel. Each row gives conversions and visits for one channel in one month. Compute each channel's overall rate as the sum of its conversions divided by the sum of its visits; do not average the monthly rates. Show the rates as percentages to one decimal place, sort channels from highest rate to lowest, label the axes 'Channel' and 'Conversion rate (%)', and title the chart 'Overall Conversion Rate by Channel'. Save the figure as figure.png.

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
3. **`/app/plotted_values.json`** - the displayed rates. Write one JSON object
   with exactly two keys: `channels`, an array of channel-name strings sorted
   from highest to lowest rate, and `conversion_rate_pct`, an equally sized
   array of JSON numbers rounded to one decimal place. For example,
   `{"channels":["Email","Search"],"conversion_rate_pct":[15.0,11.2]}`.

Do not modify `campaigns.csv`. Compute the rates from pooled conversion and
visit totals, and generate the sidecar from the same values used in the bars.

Only the libraries already installed are available and there is no network
access; everything you need is in the image.
