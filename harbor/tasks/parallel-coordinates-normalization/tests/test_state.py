"""Verifier for this task.  Runs as root in the agent's container after the
agent phase; /app is the agent's finished workspace and /tests is this
directory, copied in after the agent finished.  The agent never saw it -- but
at verify time both directories are writable, so if you re-run the agent's
script from here, keep this file off its import path: it is the answer key.

The shared artifact checks below are followed by assertions for this task's
data values and chart requirements, so an empty or unrelated submission fails.

What you can reach from here, cheapest first:
  * the delivered files (exists, size, decodes, parses)
  * the agent's own script, whose source can be checked without running it
  * anything you can compute from the input data yourself

What a PNG will NOT tell you: bar heights, tick text, series identity.  Say so
in your report; you are not required to solve it.
"""

import ast
import hashlib
import json
import os
from pathlib import Path

import pytest

APP = Path(os.environ.get("HARBOR_APP_DIR", "/app")).resolve()
FIGURE = APP / "figure.png"           # the figure required by this task
SIDECAR = APP / "plotted_values.json"  # required: ASSIGNMENT.md, Part 3
SCRIPT = APP / "plot.py"
CSV = APP / "systems.csv"
INPUT_SHA256 = "7d1ccdf8a411ad670370dd1ff37f283b969e475327ecd7c6f15770149b485ac0"
METRICS = ["latency_ms", "error_rate_pct", "throughput_mbps", "energy_wh"]
EXPECTED_SYSTEMS = [
    ("Reference A", "Reference", [1, 0.5, 0, 1]),
    ("Reference B", "Reference", [50 / 70, 4 / 6, 10 / 60, 0.8]),
    ("Reference C", "Reference", [30 / 70, 5 / 6, 20 / 60, 0.6]),
    ("Reference D", "Reference", [10 / 70, 1, 30 / 60, 0.4]),
    ("Candidate A", "Candidate", [40 / 70, 1 / 6, 40 / 60, 0.2]),
    ("Candidate B", "Candidate", [20 / 70, 2 / 6, 50 / 60, 0.3]),
    ("Candidate C", "Candidate", [0, 0, 1, 0]),
    ("Candidate D", "Candidate", [60 / 70, 1.5 / 6, 45 / 60, 0.1]),
]
EXPECTED_RANGES = {
    "latency_ms": [50, 120], "error_rate_pct": [1, 7],
    "throughput_mbps": [40, 100], "energy_wh": [3, 8],
}


# --------------------------------------------------------------- worked checks
def test_figure_exists():
    assert FIGURE.exists(), f"no figure at {FIGURE}; the task requires one"


def test_figure_is_a_valid_nonblank_png():
    """Catches a truncated write, a saved-but-empty axes, and a wrong format."""
    import numpy as np
    from PIL import Image

    size = FIGURE.stat().st_size
    assert size > 1000, f"{FIGURE} is only {size} bytes, so it is not a real chart"
    with Image.open(FIGURE) as image:
        image.verify()          # decodes the whole file; raises on corruption
    with Image.open(FIGURE) as image:
        assert image.format == "PNG", f"{FIGURE} is a {image.format}, not a PNG"
        assert min(image.size) > 100, f"{FIGURE} is {image.size}, too small to read"
        pixels = np.asarray(image.convert("RGB")).reshape(-1, 3)
    distinct = len(np.unique(pixels, axis=0))
    assert distinct > 4, f"{FIGURE} has {distinct} distinct colours: it is a blank canvas"


def test_sidecar_parses_and_has_the_promised_shape():
    """If your instruction.md promises a JSON sidecar, hold it to its schema."""
    if SIDECAR is None:
        pytest.skip("this task does not ask for a sidecar")
    assert SIDECAR.exists(), f"no {SIDECAR}; instruction.md asks for it"
    declared = json.loads(SIDECAR.read_text())   # raises on malformed JSON
    assert isinstance(declared, dict), f"{SIDECAR} holds a {type(declared).__name__}, expected an object"
    assert declared, f"{SIDECAR} is an empty object"
    # The task-specific check below validates the exact keys and nested types.


# ------------------------------------------------------------------- your checks
def test_input_was_not_modified():
    assert CSV.is_file(), f"missing input file {CSV}"
    assert hashlib.sha256(CSV.read_bytes()).hexdigest() == INPUT_SHA256


def test_independent_minmax_values_and_axis_ranges():
    declared = json.loads(SIDECAR.read_text())
    assert set(declared) == {"metrics", "ranges", "systems"}
    assert declared["metrics"] == METRICS
    assert declared["ranges"] == EXPECTED_RANGES
    actual = declared["systems"]
    assert len(actual) == len(EXPECTED_SYSTEMS)
    for row, (name, cohort, normalized) in zip(actual, EXPECTED_SYSTEMS):
        assert set(row) == {"name", "cohort", "normalized"}
        assert row["name"] == name
        assert row["cohort"] == cohort
        assert row["normalized"] == pytest.approx(normalized)
        assert all(isinstance(v, (int, float)) and not isinstance(v, bool)
                   for v in row["normalized"])


def test_plot_script_uses_parallel_coordinates_and_required_labels():
    assert SCRIPT.is_file(), f"no plotting script at {SCRIPT}"
    tree = ast.parse(SCRIPT.read_text())
    call_names = {
        node.func.attr if isinstance(node.func, ast.Attribute)
        else node.func.id if isinstance(node.func, ast.Name) else ""
        for node in ast.walk(tree) if isinstance(node, ast.Call)
    }
    string_literals = {
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    y_ticks = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "set_yticks" and node.args
    )
    title = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "set_title" and node.args
    )
    assert {"plot", "legend", "set_xticks", "set_yticks", "set_title", "savefig"} <= call_names
    assert {"systems.csv", "figure.png", *METRICS,
            "Reference", "Candidate",
            "System Profiles (Column-wise Min-Max Scaling)"} <= string_literals
    assert ast.literal_eval(y_ticks.args[0]) == [0, 0.5, 1]
    assert ast.literal_eval(title.args[0]) == "System Profiles (Column-wise Min-Max Scaling)"
    source = SCRIPT.read_text()
    assert "ranges[metric][0]" in source and "ranges[metric][1]" in source
