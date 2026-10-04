"""Run installed coding runtimes against loopback protocol fixtures; no paid provider calls."""

import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from aedrova.agents.managed import BuildAccess
from aedrova.agents.runtime import LocalRunner

requests = []
tool_calls = set()
project_path = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        requests.append(
            {
                "path": self.path,
                "model": body.get("model"),
                "beta": self.headers.get("anthropic-beta", ""),
                "tools": [
                    {"type": t.get("type"), "name": t.get("name")} for t in body.get("tools", [])
                ],
                "tool_results": [
                    i.get("output")
                    for i in body.get("input", [])
                    if isinstance(i, dict) and i.get("type") == "function_call_output"
                ]
                + [
                    block.get("content")
                    for message in body.get("messages", [])
                    for block in message.get("content", [])
                    if isinstance(block, dict) and block.get("type") == "tool_result"
                ],
                "authenticated": "local-build-token"
                in (self.headers.get("Authorization", "") + self.headers.get("x-api-key", "")),
            }
        )
        if "count_tokens" in self.path:
            data = b'{"input_tokens":100}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if "codex" in self.path:
            item = {
                "id": "msg_fixture",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {
                        "type": "output_text",
                        "text": "Managed protocol fixture complete.",
                        "annotations": [],
                    }
                ],
            }
            events = [
                {
                    "type": "response.created",
                    "response": {"id": "resp_fixture", "status": "in_progress", "output": []},
                },
                {"type": "response.output_item.added", "output_index": 0, "item": item},
                {
                    "type": "response.output_text.delta",
                    "item_id": item["id"],
                    "output_index": 0,
                    "content_index": 0,
                    "delta": item["content"][0]["text"],
                },
                {"type": "response.output_item.done", "output_index": 0, "item": item},
                {
                    "type": "response.completed",
                    "response": {
                        "id": "resp_fixture",
                        "status": "completed",
                        "output": [item],
                        "usage": {"input_tokens": 100, "output_tokens": 10, "total_tokens": 110},
                    },
                },
            ]
        else:
            events = [
                {
                    "type": "message_start",
                    "message": {
                        "id": "msg_fixture",
                        "type": "message",
                        "role": "assistant",
                        "model": body["model"],
                        "content": [],
                        "stop_reason": None,
                        "stop_sequence": None,
                        "usage": {"input_tokens": 100, "output_tokens": 0},
                    },
                },
                {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {"type": "text", "text": ""},
                },
                {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": "Managed protocol fixture complete."},
                },
                {"type": "content_block_stop", "index": 0},
                {
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                    "usage": {"output_tokens": 10},
                },
                {"type": "message_stop"},
            ]
        provider = "codex" if "codex" in self.path else "claude_code"
        if body.get("tools") and provider not in tool_calls:
            tool_calls.add(provider)
            if provider == "codex":
                item = {
                    "id": "fc_fixture",
                    "type": "function_call",
                    "call_id": "call_fixture",
                    "name": "exec_command",
                    "arguments": json.dumps(
                        {
                            "cmd": "printf %s 'local tool passed' > managed-proof-codex.txt",
                            "workdir": str(project_path),
                            "yield_time_ms": 5000,
                            "max_output_tokens": 1000,
                        }
                    ),
                }
                events = [
                    {
                        "type": "response.created",
                        "response": {"id": "resp_tool", "status": "in_progress", "output": []},
                    },
                    {"type": "response.output_item.added", "output_index": 0, "item": item},
                    {"type": "response.output_item.done", "output_index": 0, "item": item},
                    {
                        "type": "response.completed",
                        "response": {
                            "id": "resp_tool",
                            "status": "completed",
                            "output": [item],
                            "usage": {
                                "input_tokens": 100,
                                "output_tokens": 10,
                                "total_tokens": 110,
                            },
                        },
                    },
                ]
            else:
                events = [
                    events[0],
                    {
                        "type": "content_block_start",
                        "index": 0,
                        "content_block": {
                            "type": "tool_use",
                            "id": "tool_fixture",
                            "name": "Write",
                            "input": {},
                        },
                    },
                    {
                        "type": "content_block_delta",
                        "index": 0,
                        "delta": {
                            "type": "input_json_delta",
                            "partial_json": json.dumps(
                                {
                                    "file_path": str(
                                        project_path / "managed-proof-claude_code.txt"
                                    ),
                                    "content": "local tool passed",
                                }
                            ),
                        },
                    },
                    {"type": "content_block_stop", "index": 0},
                    {
                        "type": "message_delta",
                        "delta": {"stop_reason": "tool_use", "stop_sequence": None},
                        "usage": {"output_tokens": 10},
                    },
                    {"type": "message_stop"},
                ]
        data = "".join(
            "event: " + e["type"] + "\ndata: " + json.dumps(e) + "\n\n" for e in events
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main(*, verify_claude_edits=True):
    global project_path
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    report = {}
    try:
        with TemporaryDirectory(prefix="aedrova-managed-probe-") as folder:
            project_path = Path(folder)
            subprocess.run(["git", "init", "-q", folder], check=True)
            for provider, model in [
                ("codex", "gpt-5.3-codex"),
                ("claude_code", "claude-sonnet-5-5"),
            ]:
                runner = LocalRunner(print, lambda _tool, _data: True, timeout=30)
                runner.failure = lambda message: RuntimeError(str(message))
                runner.managed = BuildAccess(
                    "fixture",
                    provider,
                    model,
                    origin + "/gateway/" + provider + ("/v1" if provider == "codex" else ""),
                    "local-build-token",
                )
                try:
                    report[provider] = runner.run(
                        provider,
                        folder,
                        "Write a synthetic local proof file and confirm.",
                        plan=False,
                    )
                    if (provider != "claude_code" or verify_claude_edits) and (
                        project_path / ("managed-proof-" + provider + ".txt")
                    ).read_text() != "local tool passed":
                        raise AssertionError("Local tool output missing")
                except Exception as exc:
                    report[provider] = type(exc).__name__ + ": " + str(exc)
    finally:
        server.shutdown()
        server.server_close()
    report["requests"] = requests
    Path("work/managed-protocol.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if any(not report[p].startswith("Managed protocol fixture") for p in ("codex", "claude_code")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
