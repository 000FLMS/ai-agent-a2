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

import numpy as np
import pytest
from PIL import Image

APP = Path(os.environ.get("HARBOR_APP_DIR", "/app")).resolve()
FIGURE = APP / "figure.png"
SCRIPT = APP / "plot.py"
SIDECAR = APP / "plotted_values.json"
CSV = APP / "transactions.csv"

# Hand-derived from the eight input rows, independent of plot.py.
EXPECTED_DATES = ["2025-02-01", "2025-02-02", "2025-02-03"]
EXPECTED_SERIES = {
    "Widget A": [8, 13, 17],
    "Widget B": [5, 4, 15],
}
INPUT_SHA256 = "d4c3021ae23982a6aca8371ba6f42eb0a02d1532f581d8aa96b2557d6c0c46f3"


def test_input_was_not_modified():
    assert CSV.is_file(), f"missing input file {CSV}"
    digest = hashlib.sha256(CSV.read_bytes()).hexdigest()
    assert digest == INPUT_SHA256, "transactions.csv was changed"


def test_figure_is_a_valid_nonblank_png():
    assert FIGURE.is_file(), f"no figure at {FIGURE}"
    size = FIGURE.stat().st_size
    assert size > 1000, f"{FIGURE} is only {size} bytes"
    with Image.open(FIGURE) as image:
        image.verify()
    with Image.open(FIGURE) as image:
        assert image.format == "PNG", f"expected PNG, got {image.format}"
        assert min(image.size) > 100, f"figure is too small: {image.size}"
        pixels = np.asarray(image.convert("RGB")).reshape(-1, 3)
    distinct = len(np.unique(pixels, axis=0))
    assert distinct > 4, f"figure appears blank ({distinct} distinct colors)"


def test_plotted_values_match_the_hand_derived_answer():
    assert SIDECAR.is_file(), f"no sidecar at {SIDECAR}"
    payload = json.loads(SIDECAR.read_text())
    assert isinstance(payload, dict)
    assert set(payload) == {"dates", "series"}
    assert payload["dates"] == EXPECTED_DATES

    series = payload["series"]
    assert isinstance(series, dict)
    assert set(series) == set(EXPECTED_SERIES)
    for product, expected in EXPECTED_SERIES.items():
        values = series[product]
        assert isinstance(values, list), f"{product} values must be an array"
        assert len(values) == len(EXPECTED_DATES)
        assert all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in values
        ), f"{product} values must be JSON numbers"
        assert values == pytest.approx(expected), (
            f"wrong cumulative values for {product}: {values}"
        )


def test_plot_script_declares_the_required_line_chart():
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
    labels = {
        node.func.attr: ast.literal_eval(node.args[0])
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"set_xlabel", "set_ylabel", "set_title"}
        and node.args and isinstance(node.args[0], ast.Constant)
    }
    assert {"plot", "legend", "set_xlabel", "set_ylabel", "set_title", "savefig"} <= call_names
    assert {
        "transactions.csv", "figure.png", "Date", "Cumulative net sales ($)",
        "Cumulative Net Sales by Product",
    } <= string_literals
    assert labels == {
        "set_xlabel": "Date",
        "set_ylabel": "Cumulative net sales ($)",
        "set_title": "Cumulative Net Sales by Product",
    }
