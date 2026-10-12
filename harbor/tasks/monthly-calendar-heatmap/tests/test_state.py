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
CSV = APP / "incidents.csv"
INPUT_SHA256 = "ac8892de9ed98ea9b3f47f8d125f88b5b47362155302dbb6cc5e48f51ad2e7af"
EXPECTED_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
EXPECTED_WEEKS = [
    [None, None, None, None, None, 4, 0],
    [3, 0, 2, 1, 5, 6, 3],
    [7, 2, None, 4, 8, 5, 1],
    [2, 6, 4, 0, 3, 0, 5],
    [6, 3, 7, 2, 4, None, None],
]


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


def test_calendar_grid_preserves_zero_and_missing_dates():
    declared = json.loads(SIDECAR.read_text())
    assert set(declared) == {"weekdays", "weeks"}
    assert declared["weekdays"] == EXPECTED_WEEKDAYS
    assert declared["weeks"] == EXPECTED_WEEKS
    assert len(declared["weeks"]) == 5
    assert all(len(week) == 7 for week in declared["weeks"])
    assert all(
        value is None or (isinstance(value, int) and not isinstance(value, bool))
        for week in declared["weeks"] for value in week
    )


def test_plot_script_uses_annotated_calendar_heatmap_requirements():
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
    weekday_ticks = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "set_xticks" and len(node.args) > 1
    )
    labels = {
        node.func.attr: ast.literal_eval(node.args[0])
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"set_title", "set_label"}
        and node.args and isinstance(node.args[0], ast.Constant)
    }
    assert {"imshow", "text", "colorbar", "set_title", "set_label", "savefig"} <= call_names
    assert {
        "incidents.csv", "figure.png", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
        "Incidents", "Daily Incidents, February 2025",
    } <= string_literals
    assert ast.literal_eval(weekday_ticks.args[1]) == EXPECTED_WEEKDAYS
    assert labels == {
        "set_title": "Daily Incidents, February 2025",
        "set_label": "Incidents",
    }
