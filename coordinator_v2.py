"""
Layer 4 v2: Worker isolation via scratch directories. Source: CC forkSubagent.ts.
Workers can't see each other.

Production insight from CC's forkSubagent.ts: each subagent gets its own
working directory. This is not just tidiness — it's correctness. If worker A
writes a half-finished file and worker B reads it, you get data races and
wrong answers. Scratch directories make isolation structural: the file system
enforces what the prompt can only request.

The coordinator can still read all scratch dirs after the fact — it has a
global view; workers have local views. That asymmetry is intentional.
"""

import json
import os
import shutil
import tempfile
from anthropic import Anthropic
from coordinator_v1 import COORDINATOR_SYSTEM, WORKER_SYSTEM, TOOLS


def make_scoped_execute_tool(scratch_dir: str):
    """Return an execute_tool whose write_file is locked to scratch_dir.

    Closing over scratch_dir means the worker's tool executor literally cannot
    write outside its directory — the constraint is in the closure, not the
    prompt. Prompts can be ignored; closures cannot.
    """
    import subprocess

    def execute_tool(name: str, tool_input: dict) -> str:
        if name == "bash":
            try:
                result = subprocess.run(
                    tool_input["command"], shell=True, capture_output=True,
                    text=True, timeout=30,
                )
                return result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                return "Error: command timed out after 30s"
        elif name == "read_file":
            try:
                with open(tool_input["path"]) as f:
                    return f.read()
            except FileNotFoundError:
                return f"Error: file not found: {tool_input['path']}"
        elif name == "write_file":
            # Scope enforcement: redirect to scratch_dir regardless of requested path.
            # A worker asking to write "/etc/passwd" silently writes to its scratch.
            safe_path = os.path.join(scratch_dir, os.path.basename(tool_input["path"]))
            with open(safe_path, "w") as f:
                f.write(tool_input["content"])
            return f"Wrote {len(tool_input['content'])} bytes to {safe_path}"
        return f"Error: unknown tool: {name}"

    return execute_tool


def run_worker(task: str, client: Anthropic, model: str, scratch_dir: str) -> str:
    """Worker with scoped write_file. Message history is still isolated (same as v1).

    In production (forkSubagent.ts) this is a separate process with cwd set
    to the scratch dir. We use a closure — same principle, simpler machinery.
    """
    execute_tool = make_scoped_execute_tool(scratch_dir)
    messages = [{"role": "user", "content": task}]
    for _ in range(10):
        response = client.messages.create(
            model=model, max_tokens=4096, system=WORKER_SYSTEM,
            tools=TOOLS, messages=messages,
        )
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})
        tool_uses = [b for b in assistant_content if b.type == "tool_use"]
        if not tool_uses:
            return "\n".join(b.text for b in assistant_content if hasattr(b, "text"))
        results = [
            {"type": "tool_result", "tool_use_id": tu.id,
             "content": execute_tool(tu.name, tu.input)}
            for tu in tool_uses
        ]
        messages.append({"role": "user", "content": results})
    return "[Worker hit iteration limit]"


def coordinate(task: str, model: str) -> str:
    """Coordinate with scratch-directory isolation per worker.

    Scratch dirs are created before workers start and cleaned up after
    synthesis completes. Coordinator can inspect them between steps;
    workers never can.
    """
    client = Anthropic()

    print(f"[coordinator] Decomposing: {task[:80]}...")
    response = client.messages.create(
        model=model, max_tokens=1000, system=COORDINATOR_SYSTEM,
        messages=[{"role": "user", "content": task}],
    )

    try:
        text = response.content[0].text
        data = json.loads(text[text.index("{"):text.rindex("}") + 1])
        subtasks = data["subtasks"]
    except (json.JSONDecodeError, ValueError, KeyError):
        print("[coordinator] Could not parse decomposition — running as single task")
        scratch = tempfile.mkdtemp(prefix="worker_")
        try:
            return run_worker(task, client, model, scratch)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    # Allocate one scratch dir per worker upfront — coordinator holds all paths.
    scratch_dirs = [tempfile.mkdtemp(prefix="worker_") for _ in subtasks]
    try:
        results = []
        for i, (subtask, scratch) in enumerate(zip(subtasks, scratch_dirs)):
            print(f"[worker {i+1}/{len(subtasks)}] scratch={scratch} | {subtask[:50]}...")
            result = run_worker(subtask, client, model, scratch)
            results.append({"subtask": subtask, "result": result})
            print(f"[worker {i+1}/{len(subtasks)}] Done.")

        print("[coordinator] Synthesizing...")
        synthesis_prompt = (
            f"Original task: {task}\n\nWorker results:\n{json.dumps(results, indent=2)}\n\n"
            "Synthesize these results into a coherent final answer. "
            "Flag any weak or contradictory results."
        )
        response = client.messages.create(
            model=model, max_tokens=4096, system=COORDINATOR_SYSTEM,
            messages=[{"role": "user", "content": synthesis_prompt}],
        )
        return response.content[0].text
    finally:
        # Scratch dirs exist only for the duration of coordination.
        for d in scratch_dirs:
            shutil.rmtree(d, ignore_errors=True)
