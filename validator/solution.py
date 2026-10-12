"""The validator you write. This is the only file you need to modify.

Each function evaluates a single run object and returns the errors it finds.
An empty list means that no errors were found. `validator/runner.py` defines
what a run object contains, and `ASSIGNMENT.md` defines the four error families you may report.
"""

import base64
import io
import json
import warnings

from openai import BadRequestError
from PIL import Image, UnidentifiedImageError
from validator.prediction import Error, ErrorFamily  # noqa: F401
from validator.runner import Run
from validator.model import complete, detokenize, tokenize


CONTEXT_FRACTION = 0.5
MAX_OUTPUT_TOKENS = 2048
OMISSION = "\n[... omitted to fit model context ...]\n"
COMPACTION_NOTE = "\nSome evidence may be omitted. Do not treat omissions as agent errors.\n"
#: Shrink the image's longest side by this factor each time text compaction alone
#: still overflows. The server's tokenizer does not count image tokens, so we let
#: its context errors drive downscaling instead of estimating a pixel budget.
IMAGE_DOWNSCALE_FACTOR = 0.7
#: Stop shrinking once the longest side reaches this floor; below it the figure is
#: unreadable and further retries cannot help, so we surface the overflow instead.
MIN_IMAGE_LONG_SIDE = 64



def _excerpt(text: str, tokens: list[int], limit: int) -> str:
    """Retain the beginning and end, including the run's final actions."""
    if len(tokens) <= limit:
        return text
    head = limit // 2
    tail = limit - head
    return (
        (detokenize(tokens[:head]) if head else "")
        + OMISSION
        + (detokenize(tokens[-tail:]) if tail else "")
    )


def _compact(trajectory: str, inputs: str, fixed_prompt: str) -> tuple[str, str]:
    trajectory_info = tokenize(trajectory)
    context = trajectory_info.get("max_model_len")
    if type(context) is not int or context <= 0:
        raise RuntimeError("Validator server did not report a valid max_model_len")
    trajectory_tokens = trajectory_info["tokens"]
    input_tokens = tokenize(inputs)["tokens"]
    # Reserve half the context for the image, chat template, and tokenization
    # boundary differences. Count fixed text and omission markers separately.
    fixed_tokens = tokenize(fixed_prompt + COMPACTION_NOTE + OMISSION * 2)["tokens"]
    budget = int(context * CONTEXT_FRACTION) - len(fixed_tokens) - MAX_OUTPUT_TOKENS
    if budget < 0:
        raise RuntimeError("Task instructions exceed the baseline's context budget")
    total = len(trajectory_tokens) + len(input_tokens)
    trajectory_budget = budget * len(trajectory_tokens) // max(total, 1)
    return (
        _excerpt(trajectory, trajectory_tokens, trajectory_budget),
        _excerpt(inputs, input_tokens, budget - trajectory_budget),
    )


def _downscale(data: bytes) -> bytes | None:
    """Shrink a PNG's longest side by IMAGE_DOWNSCALE_FACTOR.

    Returns the smaller PNG, or None when the image cannot be shrunk further
    (already at the floor) or cannot be decoded at all.
    """
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            width, height = image.size
            mode = image.mode
    except (UnidentifiedImageError, OSError, ValueError):
        return None
    longest = max(width, height)
    if longest <= MIN_IMAGE_LONG_SIDE:
        return None
    scale = max(MIN_IMAGE_LONG_SIDE / longest, IMAGE_DOWNSCALE_FACTOR)
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    if new_size == (width, height):
        return None
    with Image.open(io.BytesIO(data)) as image:
        if mode not in ("RGB", "RGBA", "L"):
            image = image.convert("RGB")
        resized = image.resize(new_size, Image.LANCZOS)
    buffer = io.BytesIO()
    resized.save(buffer, format="PNG")
    return buffer.getvalue()


def _context_overflow(error: BadRequestError) -> bool:
    message = str(error).lower()
    return any(phrase in message for phrase in (
        "context_length_exceeded",
        "maximum context length",
        "maximum model length",
        "maximum input length",
    ))


def _trajectory_text(messages: list[dict]) -> str:
    events = []
    for message in messages:
        if message.get("role") == "assistant":
            calls = message.get("tool_calls") or []
            for call in calls:
                function = call.get("function") or {}
                arguments = function.get("arguments", "")
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        pass
                if isinstance(arguments, dict):
                    detail = arguments.get("command") or arguments.get("code")
                    if detail is None:
                        detail = json.dumps(arguments, ensure_ascii=False)
                else:
                    detail = str(arguments)
                events.append(f"{function.get('name', 'tool')} call:\n{detail}")
        elif message.get("role") == "tool":
            content = message.get("content", "")
            try:
                result = json.loads(content) if isinstance(content, str) else content
            except json.JSONDecodeError:
                result = content
            if isinstance(result, dict) and "output" in result:
                events.append(f"tool result (exit {result.get('returncode')}):\n{result['output']}")
            else:
                events.append(f"tool result:\n{content}")
    if not events:
        events = [
            f"assistant:\n{message['content']}"
            for message in messages
            if message.get("role") == "assistant" and message.get("content")
        ]
    return "\n\n".join(events)


def make_prompt(
    task: str,
    shown_trajectory: str,
    shown_inputs: str,
    family: ErrorFamily,
    judge_def: str,
) -> str:
    if family == ErrorFamily.WRONG_DATA:
        context = (
            f"Task (source of requirements):\n{task}\n\n"
            f"Input files:\n{shown_inputs or '(none)'}\n\n"
            f"Executed trajectory:\n{shown_trajectory or '(none)'}"
        )
        evidence_rule = "Use the task and inputs for expected data; verify the plotted result."
    elif family == ErrorFamily.WRONG_CHART:
        context = (
            f"Task (source of requirements):\n{task}\n\n"
            f"Input files (for data labels and groups):\n{shown_inputs or '(none)'}\n\n"
            f"Executed trajectory (for settings not visible in the image):\n"
            f"{shown_trajectory or '(none)'}"
        )
        evidence_rule = "Only the task defines design requirements; verify the final figure."
    elif family == ErrorFamily.HARD_TO_READ:
        context = "Judge only the attached final image."
        evidence_rule = "Use only a visible reading problem as evidence."
    else:
        raise ValueError(f"No model prompt for {family}")
    
    return f"""{context}
        Check this one issue:
        {judge_def.strip()}

        {evidence_rule} Do not list correct details as evidence of failure.

        Return only JSON with keys is_fail (boolean) and reason (string), without fences.
        For no supported failure, return {{"is_fail": false, "reason": "One sentence under 30 words"}}.
        For a supported failure, set is_fail to true and give one short evidence sentence.
        """

def _strip_json_fence(content: str) -> str:
    content = content.strip()
    lines = content.splitlines()
    if not lines or not lines[0].strip().startswith("```"):
        return content

    language = lines[0].strip()[3:].strip().lower()
    if language not in ("", "json"):
        return content

    body = lines[1:]
    if body and body[-1].strip() == "```":
        body.pop()
    return "\n".join(body).strip()


def _ask(run: Run, family: ErrorFamily, judge_def: str) -> list[Error]:
    inputs = "\n".join(
        f"{name}:\n{path.read_text(errors='replace')}" for name, path in run.inputs.items()
    ) if family != ErrorFamily.HARD_TO_READ else ""
    task = run.instructions if family != ErrorFamily.HARD_TO_READ else ""
    trajectory = _trajectory_text(run.messages) if family != ErrorFamily.HARD_TO_READ else ""
    image_bytes = run.figure.read_bytes() if run.figure else None

    def ask(prompt: str, image: bytes | None) -> dict:
        content = [{"type": "text", "text": prompt}]
        if image is not None:
            encoded = base64.b64encode(image).decode()
            content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}}
            )
        return complete(
            [{"role": "user", "content": content}],
            max_tokens=MAX_OUTPUT_TOKENS,
            response_format={"type": "json_object"},
        )

    try:
        response = ask(make_prompt(task, trajectory, inputs, family, judge_def), image_bytes)
    except BadRequestError as error:
        if not _context_overflow(error):
            raise
        warnings.warn(
            f"Run {run.run_id} ({family.value}): model context exceeded; "
            f"retrying with text capped at {CONTEXT_FRACTION:.0%} of server context.",
            stacklevel=2,
        )
        shown_trajectory, shown_inputs = _compact(
            trajectory, inputs, make_prompt(task, "", "", family, judge_def)
        )
        prompt = make_prompt(task, shown_trajectory, shown_inputs, family, judge_def) + COMPACTION_NOTE
        # Compacted text still overflows only when the image dominates the context.
        # Downscale it in place, retrying until the server accepts it or the figure
        # reaches a floor below which it would be unreadable anyway.
        image = image_bytes
        while True:
            try:
                response = ask(prompt, image)
                break
            except BadRequestError as retry_error:
                if not _context_overflow(retry_error):
                    raise
                smaller = _downscale(image) if image is not None else None
                if smaller is None:
                    raise
                with Image.open(io.BytesIO(smaller)) as shrunk:
                    new_size = shrunk.size
                warnings.warn(
                    f"Run {run.run_id} ({family.value}): still over context; "
                    f"downscaling figure to {new_size[0]}x{new_size[1]} and retrying.",
                    stacklevel=2,
                )
                image = smaller
    content = response["choices"][0]["message"]["content"]
    content = _strip_json_fence(content)
    finish_reason = response["choices"][0].get("finish_reason")
    usage = response.get("usage")
    try:
        answer = json.loads(content)
    except json.JSONDecodeError as error:
        preview = content[:160].replace("\n", "\\n")
        raise ValueError(
            f"Invalid validator JSON for run {run.run_id} ({family.value}); "
            f"finish_reason={finish_reason!r}, usage={usage!r}, line={error.lineno}, "
            f"column={error.colno}, content_prefix={preview!r}"
        ) from error
    if not isinstance(answer, dict) or type(answer.get("is_fail")) is not bool:
        raise ValueError(f"Invalid validator decision for run {run.run_id}: {content!r}")
    if not answer["is_fail"]:
        return []
    evidence = answer.get("reason")
    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError(f"Invalid validator reason for run {run.run_id}: {content!r}")
    return [Error(family=family, evidence=evidence)]



def judge_execution(run: Run) -> list[Error]:
    """Whether the run produced a figure to judge at all."""
    
    # judge_def = """
    # Based on the provided trajectory and image: 
    # Check if the agent failed to produce a valid figure in the end.
    # Should check if the needed figure image provided in the context, 
    # if trajectory shown but no real image in the context, still as failure.
    # Should only judge by final figure image, other failures should not count.
    # """
    if run.figure is None:
        return [Error(family=ErrorFamily.EXECUTION_FAILURE, evidence="No figure produced")]
    return []

def judge_data_and_chart(run: Run) -> list[Error]:
    """Whether the figure plots the requested data, built the requested way."""
    data_judge_def = """
    Does the figure show the requested data? Check incorrect values or formulas
    (including values encoded by size, color, or error bars), missing or extra
    points or series, wrong selection or aggregation, and explicitly requested
    data order or panel assignment. Derive expected data from the task and inputs;
    use executed commands as evidence, then check the final image. Do not infer
    a numerical error from an approximate pixel position when exact data agrees.
    Titles, axis settings, chart form, and styles alone are not data errors.
    """

    chart_judge_def = """
    Does the figure follow the task's explicit design requirements? Check chart
    type and projection, subplot layout and size, axes and scales, required text,
    legends and annotations, and specified colors or styles. Use the image for
    visible properties and executed commands for settings such as figure size or
    DPI. A request to add a title does not specify its wording; a request that
    text contain a word is satisfied when that word appears. For a failure,
    identify one required property and the different rendered property.
    """
    
    wrong_data = _ask(
            run,
            ErrorFamily.WRONG_DATA,
            data_judge_def,
        )
    
    wrong_chart = _ask(
            run,
            ErrorFamily.WRONG_CHART,
            chart_judge_def,
        )
    
    return wrong_data + wrong_chart


def judge_readability(run: Run) -> list[Error]:
    judge_def = """
    From the image alone, is important text or plotted content genuinely hard to
    read? Check text cut by the image edge, overlapping labels, content hidden by
    a legend or annotation, low contrast or invisible marks, indistinguishable
    series, and severely compressed panels or text too small to decipher.
    Text near an edge is not clipped when its characters remain visible.
    Name the affected element and the visible problem; do not infer one from
    rotation, density, or position alone.
    """
        
    return _ask(
        run,
        ErrorFamily.HARD_TO_READ,
        judge_def,
    )


def validate(run: Run) -> list[Error]:
    """Everything wrong with one run."""
    execution = judge_execution(run)
    if execution:
        return execution
    return judge_data_and_chart(run) + judge_readability(run)
