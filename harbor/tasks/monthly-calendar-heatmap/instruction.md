# monthly-calendar-heatmap

<!-- Copied from tasks/monthly-calendar-heatmap/task.json. This is the prompt the three fixed agents
     were given, so do NOT reword it: check-submission holds both your runs
     and this file to the descriptor's wording. Add what your verifier needs
     under the heading below instead. -->

Read incidents.csv and make a calendar heatmap for February 2025. Use a Monday-first 7-column grid labeled Mon through Sun. Position each observed date in its correct weekday column and calendar week row. Encode incident_count with both cell color and an integer annotation; observed zero counts must display 0. The date 2025-02-12 has no row and is missing: leave its cell blank with no annotation, rather than treating it as zero. Leave dates outside February blank. Include a colorbar labeled 'Incidents', title the chart 'Daily Incidents, February 2025', and keep all weekday labels and cell annotations readable. Save the figure as figure.png.

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
3. **`/app/plotted_values.json`** - the calendar grid used to draw the figure.
   Write one JSON object with exactly two keys: `weekdays`, an array of the
   strings `Mon` through `Sun`, and `weeks`, an array of five arrays of seven
   integers or `null`. Use `null` for dates outside February and for the
   missing February 12 observation; preserve observed zeros as `0`. For
   example, `{"weekdays":["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],"weeks":[[null,null,null,null,null,4,0],...]}`.

Do not modify `incidents.csv`. Read the input file and generate the sidecar
from the same grid used to draw the heatmap.

Only the libraries already installed are available and there is no network access; everything you need is in the image.
