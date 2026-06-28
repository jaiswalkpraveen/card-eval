"""
generate.py — STEP 1: turn a prompt into card text.

This is the "LLM #1" box in the flow diagram.

- Mock mode (Phase 3): return a canned card built from the prompt's expected
  attributes. Free, instant, deterministic. Proves the pipeline without a model.
- Real mode (Phase 4): ask the real LLM to write the card.
"""

import os

from llm import is_mock, get_chat_model


def _degraded_ids() -> set:
    """
    DEMO TOGGLE. Set DEGRADE to a comma-separated list of prompt ids (or "auto")
    to deliberately weaken those cards. This makes the eval surface real,
    explainable score drops vs the baseline — useful for demoing that the
    regression gate and report actually catch quality loss. Off by default.

    Examples:
        DEGRADE=auto                       # degrade a small fixed demo set
        DEGRADE=birthday-coworker,holiday-team
    """
    raw = os.getenv("DEGRADE", "").strip()
    if not raw:
        return set()
    if raw.lower() == "auto":
        return {"birthday-coworker", "holiday-team", "sympathy-coworker"}
    return {x.strip() for x in raw.split(",") if x.strip()}


def _mock_card(prompt_obj: dict, degrade: bool = False) -> str:
    """Build a believable canned card from the expected attributes."""
    if degrade:
        # Off-tone, generic, ignores occasion/recipient -> judge scores it lower.
        return "Congrats!! Buy now and save big on our limited-time offer today!!!"
    expect = prompt_obj.get("expect", {})
    occasion = expect.get("occasion", "special day")
    recipient = expect.get("recipient", "friend")
    return (
        f"Wishing you a wonderful {occasion}! "
        f"To a {recipient} who means so much — your kindness and effort never "
        f"go unnoticed. May this {occasion} bring you joy and warm memories."
    )


def generate_card(prompt_obj: dict) -> str:
    """Given one prompt object from prompts.json, return card text."""
    degrade = prompt_obj.get("id") in _degraded_ids()

    if is_mock():
        return _mock_card(prompt_obj, degrade=degrade)

    # Real mode (Phase 4)
    model = get_chat_model()
    if degrade:
        # Intentionally weak instruction so the output quality drops.
        instruction = (
            "Write one extremely short, generic, salesy greeting in under 10 words. "
            "Ignore the specific occasion, recipient, and tone.\n\n"
            f"Request: {prompt_obj['prompt']}"
        )
    else:
        instruction = (
            "Write a short greeting card (2-4 sentences). "
            "Match the occasion, recipient, and tone described.\n\n"
            f"Request: {prompt_obj['prompt']}"
        )
    response = model.invoke(instruction)
    return response.content.strip()
