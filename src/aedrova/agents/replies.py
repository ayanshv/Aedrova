"""Tool-free text replies through the existing metered, workspace-scoped gateway."""

import asyncio
import json

import httpx

from aedrova.agents.runtime import BuildCancelled


def needs_sources(question):
    """Keep general conversation out of workspace/connector retrieval.

    Explicit source questions and ambiguous follow-ups retain the evidence path.
    This only selects read-only retrieval, never authorizes a build or tool action.
    """
    import re

    # Non-English requests can refer to the same English workspace evidence.
    # Greetings stay fast; unknown non-Latin questions retain read-only context.
    greetings = {
        "नमस्ते",
        "हैलो",
        "हेलो",
        "नमस्ते Aedrova",
        "नमस्कार",
        "हाय",
        "سلام",
        "مرحبا",
        "你好",
        "こんにちは",
        "안녕하세요",
        "สวัสดี",
    }
    if any(ord(c) > 0x024F for c in question):
        return question.strip().strip("!।。?？ ") not in greetings
    return bool(
        re.search(
            r"\b(workspace|chatspace|channels?|messages?|chats?|files?|meetings?|transcripts?|"
            r"project|codebase|folder|repositories|repository|repos?|commits?|deployments?|"
            r"pull requests?|issues?|"
            r"github|supabase|figma|notion|stripe|instagram|tiktok|vercel|search|"
            r"research|investigate|investigation|current|today|sources|fact.check|"
            r"revenue|balance|customers?|analytics|metrics|latest|recent|changed|updates?|"
            r"our team|our project|our product|what we|what did|that|those|above)\b",
            question,
            re.IGNORECASE,
        )
    )


def reply(access, prompt, cancelled, emit=lambda _text: None, *, timeout=90):
    """No local process, tools, implicit retries or shared provider key.

    The gateway retains membership checks, reservations and conservative settlement.
    Poll cancellation even when the upstream connection is waiting for its first byte.
    """
    return asyncio.run(_reply(access, prompt, cancelled, emit, timeout))


async def _reply(access, prompt, cancelled, emit, timeout):
    if cancelled.is_set():
        raise BuildCancelled()
    if len(prompt.encode()) > 240000:
        raise ValueError("This question has too much context. Try a narrower request.")
    limit = min(4096, access.limits.get("output_tokens", 4096))
    language_instruction = (
        "Respond in the language of the current user question, including mixed-language "
        "questions. Preserve code, citations and proper names."
    )
    if access.provider == "codex":
        path = "/responses"
        body = {
            "model": access.model,
            "input": prompt,
            "instructions": language_instruction,
            "max_output_tokens": limit,
            "stream": True,
            "store": False,
            "tools": [],
        }
        if access.model.startswith("gpt-5"):
            body["reasoning"] = {"effort": "low"}
    elif access.provider == "claude_code":
        path = "/v1/messages"
        body = {
            "model": access.model,
            "messages": [{"role": "user", "content": prompt}],
            "system": language_instruction,
            "max_tokens": limit,
            "stream": True,
            "tools": [],
        }
    else:
        raise ValueError("Unsupported reply provider.")

    async def consume():
        text, complete, size, stopped = "", False, 0, False
        async with (
            httpx.AsyncClient(
                timeout=httpx.Timeout(timeout, connect=timeout),
                trust_env=False,
                follow_redirects=False,
            ) as client,
            client.stream(
                "POST",
                access.base_url + path,
                json=body,
                headers={"Authorization": "Bearer " + access.token},
            ) as response,
        ):
            if response.status_code != 200:
                raw = bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 4096:
                        break
                try:
                    message = json.loads(raw).get("error", "")
                except (ValueError, AttributeError):
                    message = ""
                if (
                    isinstance(message, str)
                    and message.startswith(
                        (
                            "Monthly AI budget reached.",
                            "Monthly AI request limit reached.",
                            "Shared five-hour AI capacity reached.",
                        )
                    )
                    and access.token not in message
                ):
                    raise RuntimeError(message[:350])
                raise RuntimeError(
                    "AI could not authorize this reply. Check your team’s plan and retry."
                )
            async for line in response.aiter_lines():
                size += len(line.encode())
                if size > 2_000_000:
                    raise RuntimeError("AI reply exceeded its safe response limit.")
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    continue
                event = json.loads(data)
                kind = event.get("type")
                if event.get("error") or kind in {
                    "error",
                    "response.failed",
                    "response.incomplete",
                }:
                    if isinstance(event.get("error"), dict) and (
                        event["error"].get("type") == "provider_error"
                    ):
                        raise RuntimeError(
                            "The selected AI provider rejected this reply. Your workspace owner "
                            "should check its credit balance and model access."
                        )
                    raise RuntimeError(
                        "AI could not finish this reply. Check provider availability and retry."
                    )
                delta = ""
                if access.provider == "codex":
                    if kind == "response.output_text.delta":
                        delta = event.get("delta", "")
                    elif kind == "response.completed":
                        complete = event.get("response", {}).get("status") == "completed"
                else:
                    if kind == "content_block_delta":
                        part = event.get("delta", {})
                        if part.get("type") == "text_delta":
                            delta = part.get("text", "")
                    elif kind == "message_delta":
                        reason = event.get("delta", {}).get("stop_reason")
                        if reason is not None and reason not in {
                            "end_turn",
                            "stop_sequence",
                        }:
                            raise RuntimeError(
                                "AI reached its reply limit. Ask for a shorter answer."
                            )
                        stopped = reason in {"end_turn", "stop_sequence"}
                    elif kind == "message_stop":
                        complete = stopped
                if not isinstance(delta, str):
                    raise ValueError("Invalid AI reply stream.")
                text += delta
                if len(text) > 20000:
                    raise ValueError(
                        "Ask for a shorter reply; this answer exceeded the chat limit."
                    )
                if delta:
                    emit(text)
        if not complete or not text.strip():
            raise RuntimeError("AI stopped before completing the reply. Please retry.")
        return text

    task = asyncio.create_task(consume())
    try:
        async with asyncio.timeout(min(timeout, access.limits.get("run_seconds", timeout))):
            while not task.done():
                if cancelled.is_set():
                    raise BuildCancelled()
                await asyncio.wait({task}, timeout=0.1)
            if cancelled.is_set():
                raise BuildCancelled()
            return await task
    except (httpx.HTTPError, TimeoutError) as exc:
        raise RuntimeError("AI is taking too long to respond. Please retry in a moment.") from exc
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
