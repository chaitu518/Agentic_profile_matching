"""Optional LLM layer (off by default).

Set LLM_PROVIDER to let an LLM (a) extract requirements from messy JDs, (b) classify messages the
rule router can't, (c) write narrative summaries, and (d) answer open questions by calling the
agent's tools itself - the same function-calling loop as Milestone 1's llm_file_assistant.py.
`openrouter` uses OPENROUTER_API_KEY / OPENROUTER_MODEL exactly like Milestone 1.

Scores never come from the LLM, so rankings stay reproducible and explainable.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from agent import config

DEFAULT_MODELS = {
    "openrouter": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5",
    "groq": "llama-3.3-70b-versatile",
    "google": "gemini-2.0-flash",
    "ollama": "llama3.1",
}


@lru_cache(maxsize=1)
def get_llm():
    provider = config.LLM_PROVIDER
    if not provider:
        return None
    model = config.LLM_MODEL or DEFAULT_MODELS.get(provider, "")
    try:
        if provider == "openrouter":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model, temperature=0, base_url="https://openrouter.ai/api/v1",
                              api_key=os.environ["OPENROUTER_API_KEY"])
        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model, temperature=0)
        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=model, temperature=0)
        if provider == "groq":
            from langchain_groq import ChatGroq
            return ChatGroq(model=model, temperature=0)
        if provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model, temperature=0)
        if provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(model=model, temperature=0)
    except Exception as e:
        print(f"[llm] Could not initialise {provider}: {e}. Running in deterministic mode.")
    return None


def structured(prompt: str, schema):
    llm = get_llm()
    if llm is None:
        return None
    try:
        return llm.with_structured_output(schema).invoke(prompt)
    except Exception as e:
        print(f"[llm] structured call failed: {e}")
        return None


def narrate(prompt: str) -> str | None:
    llm = get_llm()
    if llm is None:
        return None
    try:
        return llm.invoke(prompt).content
    except Exception as e:
        print(f"[llm] narrate failed: {e}")
        return None


def tool_loop(question: str, tools: list, system: str, max_steps: int = 6, llm=None) -> tuple[str | None, list[dict]]:
    """Milestone-1-style loop: the model picks tools, we run them, feed results back, repeat.
    Returns (answer, trace). (None, []) when no LLM is configured."""
    from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

    llm = llm or get_llm()
    if llm is None:
        return None, []
    by_name = {t.name: t for t in tools}
    bound = llm.bind_tools(tools)
    msgs = [SystemMessage(content=system), HumanMessage(content=question)]
    trace: list[dict] = []
    for _ in range(max_steps):
        reply = bound.invoke(msgs)
        msgs.append(reply)
        if not getattr(reply, "tool_calls", None):
            return reply.content, trace
        for call in reply.tool_calls:
            tool = by_name.get(call["name"])
            try:
                result = tool.invoke(call["args"]) if tool else {"error": f"unknown tool {call['name']}"}
            except Exception as e:                  # errors go back to the model as data (as in Milestone 1)
                result = {"success": False, "error": f"{type(e).__name__}: {e}"}
            text = json.dumps(result, default=str)[:6000]
            trace.append({"tool": call["name"], "args": call["args"], "result": text[:120]})
            msgs.append(ToolMessage(content=text, tool_call_id=call["id"]))
    return "Stopped: too many tool steps.", trace
