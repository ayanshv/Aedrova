"""Private stdio approval transport; never grants session-wide escalation."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from aedrova.agents.permissions import normalize


def run(runner, project, prompt, *, plan, command, env):
    from aedrova.agents.runtime import BuildCancelled, pipe_events, stop_process

    configs = []
    for index, arg in enumerate(command[:-1]):
        if arg == "-c" and not command[index + 1].startswith("approval_policy="):
            configs.extend(["-c", command[index + 1]])
    selected = normalize(runner.permission_mode)
    with TemporaryDirectory(prefix="aedrova-approval-runtime-") as home:
        os.chmod(home, 0o700)
        if not runner.managed:
            # Copy authentication only, never personal config, rules, MCPs or hooks.
            source = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json"
            if source.is_file():
                destination = Path(home) / "auth.json"
                shutil.copyfile(source, destination)
                destination.chmod(0o600)
        clean = {**env, "CODEX_HOME": home}
        process = subprocess.Popen(
            [command[0], "app-server", *configs, "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=clean,
            start_new_session=True,
            **(
                {"pass_fds": (runner.lease_fd,)}
                if runner.lease_fd is not None and sys.platform != "win32"
                else {}
            ),
        )
        runner.process = process
        started = time.monotonic()
        pending, diagnostics = b"", b""
        thread, turn, final = None, None, ""
        item_details = {}
        tools = set()
        next_id = 3
        requests = {1: "initialize"}
        job = None

        def send(value):
            process.stdin.write(json.dumps(value).encode() + b"\n")
            process.stdin.flush()

        try:
            if sys.platform == "win32":
                from aedrova.agents.windows_job import WindowsJob

                job = WindowsJob(process)
                runner.job = job
            send(
                {
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "clientInfo": {"name": "aedrova", "version": "1.0.0"},
                    },
                }
            )
            events = pipe_events(process)
            try:
                for stream, data in events:
                    if runner.cancelled.is_set():
                        raise BuildCancelled()
                    if time.monotonic() - started > runner.timeout:
                        raise TimeoutError("Build exceeded its configured time limit.")
                    if stream is None:
                        continue
                    if stream is process.stderr:
                        diagnostics = (diagnostics + data)[-16384:]
                        continue
                    pending += data
                    if len(pending) > 2 * 1024 * 1024:
                        raise ValueError("Provider event exceeded its size limit.")
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        try:
                            event = json.loads(line)
                        except ValueError:
                            continue
                        if not isinstance(event, dict):
                            continue
                        if "method" not in event:
                            phase = requests.pop(event.get("id"), None)
                            if event.get("error"):
                                raise runner.failure(str(event["error"]))
                            if phase == "initialize":
                                send({"method": "initialized", "params": {}})
                                requests[2] = "thread"
                                send(
                                    {
                                        "id": 2,
                                        "method": "thread/start",
                                        "params": {
                                            "cwd": str(project),
                                            "ephemeral": True,
                                            "approvalPolicy": "never"
                                            if selected == "full"
                                            else "untrusted",
                                            "approvalsReviewer": "user",
                                            "baseInstructions": (
                                                "You are Aedrova. "
                                                "Follow the supplied build instructions. "
                                                "Do not access secrets, publish "
                                                "or change permissions."
                                            ),
                                        },
                                    }
                                )
                            elif phase == "thread":
                                thread = event["result"]["thread"]["id"]
                                requests[next_id] = "turn"
                                send(
                                    {
                                        "id": next_id,
                                        "method": "turn/start",
                                        "params": {
                                            "threadId": thread,
                                            "input": [{"type": "text", "text": prompt}],
                                        },
                                    }
                                )
                                next_id += 1
                            elif phase == "turn":
                                turn = event["result"]["turn"]["id"]
                            continue
                        method, params = event["method"], event.get("params") or {}
                        if "id" in event:
                            # Unknown/new authority requests fail closed. Never acceptForSession.
                            same_scope = (
                                bool(thread and turn)
                                and params.get("threadId") == thread
                                and params.get("turnId") == turn
                            )
                            allowed = False
                            if same_scope and method in {
                                "item/commandExecution/requestApproval",
                                "item/fileChange/requestApproval",
                            }:
                                details = item_details.get(params.get("itemId"), {})
                                if method == "item/fileChange/requestApproval":
                                    paths = [
                                        row.get("path", "") for row in details.get("changes", [])
                                    ]
                                    root = Path(project).resolve()
                                    grant = Path(params.get("grantRoot") or root).resolve()
                                    from aedrova.agents.permissions import automatic

                                    valid = grant.is_relative_to(root) and automatic(
                                        "Edit", {"paths": paths}, root
                                    )
                                    if valid and not plan:
                                        allowed = runner.approve(
                                            "Edit",
                                            {"paths": paths, "changes": details.get("changes", [])},
                                        )
                                elif (
                                    not params.get("networkApprovalContext")
                                    and params.get("kind", "command") == "command"
                                ):
                                    from aedrova.agents.runtime import network_command

                                    action = params.get("command") or details.get("command") or ""
                                    if action and not network_command(action):
                                        allowed = runner.approve(
                                            "Bash",
                                            {
                                                "command": action,
                                                "cwd": params.get("cwd"),
                                                "reason": params.get("reason"),
                                            },
                                        )
                            if runner.cancelled.is_set():
                                raise BuildCancelled()
                            if method == "item/permissions/requestApproval":
                                result = {"permissions": {}, "scope": "turn"}
                            elif method in {
                                "item/commandExecution/requestApproval",
                                "item/fileChange/requestApproval",
                            }:
                                result = {"decision": "accept" if allowed else "decline"}
                            else:
                                send(
                                    {
                                        "id": event["id"],
                                        "error": {
                                            "code": -32601,
                                            "message": "Unsupported Aedrova action",
                                        },
                                    }
                                )
                                continue
                            send({"id": event["id"], "result": result})
                            continue
                        if params.get("threadId") not in {None, thread}:
                            continue
                        if method == "turn/started":
                            turn = params.get("turn", {}).get("id", turn)
                        if method in {"item/started", "item/completed"}:
                            item = params.get("item") or {}
                            identity = item.get("id")
                            item_details[identity] = item
                            kind = item.get("type")
                            if kind in {
                                "commandExecution",
                                "fileChange",
                                "mcpToolCall",
                                "webSearch",
                            }:
                                tools.add(identity)
                                if runner.managed and len(tools) > runner.managed.limits.get(
                                    "tool_calls", 200
                                ):
                                    raise RuntimeError("This workflow reached its tool limit.")
                            if method == "item/completed":
                                if kind == "agentMessage":
                                    final = item.get("text", "")
                                    runner.emit(final)
                                elif kind == "commandExecution":
                                    runner.observe_command(
                                        item.get("command", ""),
                                        item.get("aggregatedOutput", ""),
                                        item.get("exitCode"),
                                    )
                                    runner.emit(
                                        f"$ {item.get('command', '')}\n"
                                        f"{item.get('aggregatedOutput', '')[-20000:]}\n"
                                        f"Exit code: {item.get('exitCode')}"
                                    )
                                elif kind == "fileChange":
                                    runner.emit(
                                        "Files changed: " + json.dumps(item.get("changes", []))
                                    )
                        elif method == "thread/tokenUsage/updated":
                            usage = params.get("tokenUsage", {}).get("total", {})
                            runner.usage = {
                                "input_tokens": usage.get("inputTokens", 0),
                                "output_tokens": usage.get("outputTokens", 0),
                                "cached_input_tokens": usage.get("cachedInputTokens", 0),
                            }
                        elif method == "turn/completed":
                            completed = params.get("turn", {})
                            if (
                                completed.get("id") != turn
                                or completed.get("status") != "completed"
                                or not final
                            ):
                                raise runner.failure(
                                    str(completed.get("error") or "Incomplete run")
                                )
                            return final
            finally:
                events.close()
            raise runner.failure(diagnostics.decode(errors="replace"))
        finally:
            if job:
                job.close()
            stop_process(process, force=True)
            process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()
            process.stderr.close()
            runner.process = runner.job = None
