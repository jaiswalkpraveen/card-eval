"""
generate.py — STEP 1: turn a prompt into card text.

This is the "LLM #1" box in the flow diagram.

- Mock mode (Phase 3): return a canned card built from the prompt's expected
  attributes. Free, instant, deterministic. Proves the pipeline without a model.
- Real mode (Phase 4): ask the real LLM to write the card.
"""

from llm import is_mock, get_chat_model


def _mock_card(prompt_obj: dict) -> str:
    """Build a believable canned card from the expected attributes."""
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
    if is_mock():
        return _mock_card(prompt_obj)

    # Real mode (Phase 4)
    model = get_chat_model()
    instruction = (
        "Write a short greeting card (2-4 sentences). "
        "Match the occasion, recipient, and tone described.\n\n"
        f"Request: {prompt_obj['prompt']}"
    )
    response = model.invoke(instruction)
    return response.content.strip()
