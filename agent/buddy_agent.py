"""Buddy agent: talks to Claude and runs the starter tools in a bounded loop.

How it works (one run):
  1. Send Claude the system prompt, the user's task, the selected case, and
     the two tool descriptions.
  2. Claude replies with either a tool request or a final report.
  3. For a tool request: validate the tool name and case ID, run the real
     tool from tools.py, record the result, and send it back to Claude.
  4. Repeat until Claude writes the report or a limit is reached.

The model never runs anything itself. This file decides what actually runs.

Quick test from the project folder:
    python agent/buddy_agent.py calculator
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import anthropic

# tools.py lives one folder up (the project root), so make it importable.
AGENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = AGENT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools import TOOL_DESCRIPTIONS, inspect_case, run_checks  # noqa: E402

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
MODEL = "claude-opus-5-5"
MAX_TOOL_CALLS = 4      # assignment limit: at most 4 tool executions per run
MAX_MODEL_CALLS = 5     # assignment limit: at most 5 model calls per run
SUPPORTED_CASES = ["calculator", "task_counter", "average"]
REQUIRED_TOOLS = {"inspect_case", "run_checks"}  # evidence needed before a report
TOOL_FUNCTIONS = {"inspect_case": inspect_case, "run_checks": run_checks}

SYSTEM_PROMPT_FILE = AGENT_DIR / "system_prompt.txt"

# Used only until you write your own system_prompt.txt (Step 2 of the assignment).
PLACEHOLDER_PROMPT = """You are a helpful assistant that investigates a small Python program for a beginner.
Use inspect_case to read the requirements, source, and tests, and run_checks to run the tests.
Base every claim on the tool results. Never invent a bug, and never say a test passed unless run_checks shows it passed.
Finish with a short report: case and relevant requirement, test status with a short output excerpt,
most important finding, suggested next step, and one limitation."""


def load_system_prompt():
    """Read system_prompt.txt, skipping lines that start with # (notes to yourself).

    Falls back to the placeholder if the file is missing or has no real text yet.
    """
    if SYSTEM_PROMPT_FILE.exists():
        lines = SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").splitlines()
        prompt = "\n".join(ln for ln in lines if not ln.lstrip().startswith("#")).strip()
        if prompt:
            return prompt
    return PLACEHOLDER_PROMPT


# ---------------------------------------------------------------------------
# Tool definitions for Claude
# ---------------------------------------------------------------------------
def build_tools():
    """Turn the starter's TOOL_DESCRIPTIONS into Claude's tool format.

    Adds a required "reason" field so every tool request comes with a short,
    checkable explanation for the activity trace. The real tools ignore it.
    """
    tools = []
    for desc in TOOL_DESCRIPTIONS:
        schema = json.loads(json.dumps(desc["parameters"]))  # deep copy
        schema["properties"]["reason"] = {
            "type": "string",
            "description": "One short sentence: why you are calling this tool now.",
        }
        schema["required"] = ["case_id", "reason"]
        schema["additionalProperties"] = False
        tools.append({
            "name": desc["name"],
            "description": desc["description"],
            "input_schema": schema,
            "strict": True,
        })
    return tools


# ---------------------------------------------------------------------------
# Running one tool safely
# ---------------------------------------------------------------------------
def execute_tool(name, tool_input, selected_case):
    """Validate and run one tool.

    Returns (result_dict, is_error, executed). "executed" is False when the
    request was rejected before anything ran, so it doesn't use up the limit.
    """
    if name not in TOOL_FUNCTIONS:
        return {"error": f"Unknown tool '{name}'. Use inspect_case or run_checks."}, True, False

    case_id = tool_input.get("case_id") if isinstance(tool_input, dict) else None
    if case_id not in SUPPORTED_CASES:
        return {"error": f"Unsupported case ID '{case_id}'. Choose one of {SUPPORTED_CASES}."}, True, False
    if case_id != selected_case:
        # Keeps evidence from a different case out of this run's report.
        return {"error": f"This run is about '{selected_case}', not '{case_id}'."}, True, False

    try:
        result = TOOL_FUNCTIONS[name](case_id)
    except Exception as exc:  # the tool itself failed to start
        return {
            "error": f"The {name} tool failed to run: {exc}",
            "note": "This is a tool problem, NOT evidence of a bug in the sample program.",
        }, True, True

    if name == "run_checks" and result.get("status") == "timeout":
        result["note"] = "The tests did not finish. This is NOT a pass and NOT a confirmed bug."
        return result, False, True
    return result, False, True


def short_preview(name, result):
    """A one-line summary of a tool result for the activity trace."""
    if "error" in result:
        return result["error"]
    if name == "inspect_case":
        return f"Read {len(result['requirements'])} requirements, the source code, and the tests."
    if name == "run_checks":
        lines = [ln for ln in result.get("output", "").strip().splitlines() if ln.strip()]
        last = lines[-1] if lines else "(no output)"
        return f"status={result.get('status')}, exit_code={result.get('exit_code')}: {last}"
    return str(result)[:200]


# ---------------------------------------------------------------------------
# The agent loop
# ---------------------------------------------------------------------------
SECRETS_FILE = PROJECT_ROOT / ".streamlit" / "secrets.toml"


def read_api_key():
    """Find the API key: the ANTHROPIC_API_KEY environment variable first,
    then the ANTHROPIC_API_KEY line in .streamlit/secrets.toml (git-ignored)."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    if SECRETS_FILE.exists():
        for line in SECRETS_FILE.read_text(encoding="utf-8").splitlines():
            name, sep, value = line.partition("=")
            if sep and name.strip() == "ANTHROPIC_API_KEY":
                return value.strip().strip('"').strip("'")
    return None


def make_client(api_key=None):
    """Create the Claude client using the given key, or the one from read_api_key()."""
    key = api_key or read_api_key()
    if not key:
        raise anthropic.AnthropicError(
            "No API key found. Add ANTHROPIC_API_KEY to .streamlit/secrets.toml.")
    return anthropic.Anthropic(api_key=key)


def run_buddy(case_id, task, client=None):
    """Run one bounded investigation.

    Returns a dict:
      trace  - list of steps (action, reason, result preview, what happens next)
      report - the final report text, or None
      error  - a friendly error message, or None
      tool_calls / model_calls - counts used
    """
    run = {
        "case_id": case_id,
        "task": task,
        "model": MODEL,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "trace": [],
        "report": None,
        "error": None,
        "tool_calls": 0,
        "model_calls": 0,
    }

    if case_id not in SUPPORTED_CASES:
        run["error"] = f"Unsupported case '{case_id}'. Choose one of {SUPPORTED_CASES}."
        return run

    try:
        client = client or make_client()
    except anthropic.AnthropicError as exc:
        run["error"] = f"The model service is not configured: {exc}"
        return run

    tools = build_tools()
    system_prompt = load_system_prompt()
    used_tools = set()
    messages = [{
        "role": "user",
        "content": f"Selected case: {case_id}\n\nTask: {task}",
    }]

    while run["model_calls"] < MAX_MODEL_CALLS:
        # ---- 1. Ask the model what to do next ----
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=16000,
                system=system_prompt,
                tools=tools,
                messages=messages,
                output_config={"effort": "medium"},
            )
        except anthropic.AuthenticationError:
            run["error"] = "The model service rejected the API key. Check the key in your settings."
            return run
        except anthropic.RateLimitError:
            run["error"] = "The model service is busy or the usage limit was reached. Try again shortly."
            return run
        except anthropic.APIConnectionError:
            run["error"] = "Could not reach the model service. Check your internet connection."
            return run
        except anthropic.APIStatusError as exc:
            run["error"] = f"The model service returned an error ({exc.status_code}). Try again later."
            return run
        run["model_calls"] += 1

        # Keep the whole reply (including any thinking blocks) in the history.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "refusal":
            run["error"] = "The model declined this request."
            return run
        if response.stop_reason == "max_tokens":
            run["error"] = "The model's reply was cut off before it finished."
            return run

        tool_requests = [b for b in response.content if b.type == "tool_use"]

        # ---- 2a. No tool requested: this is the final answer ----
        if not tool_requests:
            text = "\n".join(b.text for b in response.content if b.type == "text").strip()
            missing = REQUIRED_TOOLS - used_tools
            if missing and run["tool_calls"] < MAX_TOOL_CALLS:
                # Don't accept a report without evidence: send the model back.
                run["trace"].append({
                    "action": "final answer (rejected)",
                    "reason": "Tried to conclude before gathering evidence.",
                    "result": f"Missing evidence from: {', '.join(sorted(missing))}",
                    "next": "Asked the model to gather the missing evidence first.",
                })
                messages.append({
                    "role": "user",
                    "content": "Before writing the report, you must call: "
                               + ", ".join(sorted(missing)) + ".",
                })
                continue
            run["report"] = text or "(The model returned an empty report.)"
            if missing:
                run["report"] += ("\n\nWarning: this report was written without evidence from "
                                  + ", ".join(sorted(missing)) + ".")
            run["trace"].append({
                "action": "final report",
                "reason": "Evidence gathered.",
                "result": "Report written.",
                "next": "Done.",
            })
            return run

        # ---- 2b. Run each requested tool and send the results back ----
        tool_results = []
        for block in tool_requests:
            tool_input = block.input if isinstance(block.input, dict) else {}
            reason = tool_input.get("reason", "(no reason given)")

            if run["tool_calls"] >= MAX_TOOL_CALLS:
                result, is_error = {"error": "Tool limit reached. Write the report now."}, True
            else:
                result, is_error, executed = execute_tool(block.name, tool_input, case_id)
                if executed:
                    run["tool_calls"] += 1
                # A timed-out test run is not real test evidence.
                if not is_error and result.get("status") != "timeout":
                    used_tools.add(block.name)

            run["trace"].append({
                "action": f"{block.name}({tool_input.get('case_id')})",
                "reason": reason,
                "result": short_preview(block.name, result),
                "raw_result": result,
                "next": "Sent this result back to the model.",
            })
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
                "is_error": is_error,
            })

        # All results go back together in one user message.
        messages.append({"role": "user", "content": tool_results})

    run["error"] = (f"Stopped after {MAX_MODEL_CALLS} model calls without a final report. "
                    "No conclusion was reached.")
    return run


# ---------------------------------------------------------------------------
# Saving runs (for the "Replay a saved run" feature)
# ---------------------------------------------------------------------------
def save_run(run, path):
    """Save a finished run to a JSON file so it can be replayed later."""
    Path(path).write_text(json.dumps(run, indent=2), encoding="utf-8")


def load_run(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Command-line test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else "calculator"
    result = run_buddy(case, "Investigate this program and explain the most important result to a beginner.")
    for i, step in enumerate(result["trace"], 1):
        print(f"{i}. {step['action']}\n   why:    {step['reason']}\n"
              f"   result: {step['result']}\n   next:   {step['next']}")
    print(f"\nModel calls: {result['model_calls']}  Tool calls: {result['tool_calls']}")
    print("\nERROR: " + result["error"] if result["error"] else "\n" + result["report"])
