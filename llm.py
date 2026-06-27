"""
llm.py — the ONE place that decides: fake LLM (mock) or real LLM.

Phase 3: MOCK is on. No network, no API key, canned answers. We use this to
prove the whole pipeline (generate -> judge -> save -> compare) works.

Phase 4: set MOCK=0 in .env and fill in OPENAI_API_BASE / OPENAI_API_KEY.
Then get_chat_model() returns a real LangChain ChatOpenAI pointed at your
OpenCode-compatible endpoint. Nothing else in the project changes.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env if present (Phase 4); harmless if absent (Phase 3)


def is_mock() -> bool:
    """
    Mock mode is ON when MOCK=1, OR when no API key is configured.
    This makes the project safe-by-default: with no key, it never hits network.
    """
    mock_flag = os.getenv("MOCK", "").strip()
    if mock_flag == "1":
        return True
    if mock_flag == "0":
        return False
    # MOCK not explicitly set: fall back to "mock unless a key exists"
    return not os.getenv("OPENAI_API_KEY")


def get_chat_model():
    """
    Return a real LangChain chat model. Only called in Phase 4 (real mode).
    Imported lazily so Phase 3 mock runs never need langchain_openai loaded.
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        base_url=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        temperature=0.7,
    )
