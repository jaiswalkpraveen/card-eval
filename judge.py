"""
judge.py — STEP 2: score a card against the rubric (LLM-as-judge).

This is the "LLM #2" box in the flow diagram.

- Mock mode (Phase 3): return canned scores. Lets the pipeline run end-to-end
  with no model. Scores are deterministic so compare.py has a stable baseline.
- Real mode (Phase 4): a second LLM reads the rubric + card and returns scores
  as strict JSON, validated by the Pydantic schema below.
"""

from pathlib import Path
from pydantic import BaseModel, Field
from llm import is_mock, get_chat_model

RUBRIC_PATH = Path(__file__).parent / "rubric.md"


class CardScore(BaseModel):
    """The strict shape every judge result must match."""

    prompt_fidelity: int = Field(ge=1, le=5)
    text_accuracy: int = Field(ge=1, le=5)
    style_consistency: int = Field(ge=1, le=5)
    aesthetic: int = Field(ge=1, le=5)
    reasoning: str

    def overall(self) -> float:
        return round(
            (
                self.prompt_fidelity
                + self.text_accuracy
                + self.style_consistency
                + self.aesthetic
            )
            / 4,
            2,
        )


def _mock_score(prompt_obj: dict, card_text: str) -> CardScore:
    """Deterministic canned scores for Phase 3."""
    return CardScore(
        prompt_fidelity=4,
        text_accuracy=5,
        style_consistency=4,
        aesthetic=4,
        reasoning="Mock score: on-occasion, correct tone, ideal card length.",
    )


def judge_card(prompt_obj: dict, card_text: str) -> CardScore:
    """Score one card. Returns a validated CardScore."""
    if is_mock():
        return _mock_score(prompt_obj, card_text)

    # Real mode (Phase 4): LLM-as-judge with structured output
    rubric = RUBRIC_PATH.read_text()
    model = get_chat_model().with_structured_output(CardScore)
    instruction = (
        "You are a strict greeting-card quality judge. Score the card using "
        "the rubric below. Return only the structured fields.\n\n"
        f"--- RUBRIC ---\n{rubric}\n\n"
        f"--- ORIGINAL REQUEST ---\n{prompt_obj['prompt']}\n"
        f"Expected attributes: {prompt_obj.get('expect', {})}\n\n"
        f"--- CARD TO SCORE ---\n{card_text}"
    )
    return model.invoke(instruction)
