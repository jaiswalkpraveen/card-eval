# card-eval

An **LLM-as-judge evaluation harness** that scores AI-generated greeting cards
against a written rubric, with a **Playwright end-to-end test** that links what a
customer actually sees (the rendered card) to its measured quality.

Built to explore a focused question: *how do you put a defensible, repeatable
number on "is this AI output good?"* instead of relying on gut feeling.

---

## What it does

1. An LLM **generates** a greeting card for each prompt (e.g. *"a birthday card
   for a coworker, warm but professional"*).
2. A second LLM **judges** that card against a rubric, scoring 4 dimensions 1-5.
3. Scores are saved; a **regression gate** flags any run that drops below
   baseline.
4. A **Playwright** test renders a generated card in a real browser and asserts
   both that it displays correctly *and* that it passes the eval threshold.

---

## The mental model (school exam)

| Piece | Role | What it is |
|-------|------|------------|
| `prompts.json` | the exam questions | input data |
| `rubric.md` | the grading guide | the eval rules |
| `generate.py` | the **student** | the AI under test (LLM #1) |
| `judge.py` | the **teacher** | LLM-as-judge (the eval, LLM #2) |
| `run_eval.py` | the **proctor** | orchestrates a full run |
| `compare.py` | the report-card check | regression gate vs baseline |
| `llm.py` | the phone line | shared connection to the model gateway |

**LLM-as-judge** = a second AI grades the first AI's output against a written
rubric, producing a repeatable numeric score instead of a subjective opinion.

---

## Architecture

```
                prompts.json  (occasion, recipient, tone)
                     |
                     v
   +----------------------------------+
   |  run_eval.py  (the proctor)      |
   |                                  |
   |   for each prompt:               |
   |                                  |
   |   generate.py ---> card text     |   LLM #1  (the student)
   |        |                         |
   |        v                         |
   |   judge.py  ----> CardScore      |   LLM #2  (the teacher)
   |        (scores 1-5 x 4 dims      |
   |         + reasoning, via         |
   |         rubric.md)               |
   +----------------------------------+
                     |
                     v
        results/baseline.json  or  results/run-<timestamp>.json
                     |
                     v
            compare.py  --> flags any drop > 0.5 vs baseline

   e2e/test_card.py (Playwright):
        generate card -> render in web/card.html (real browser)
        -> assert it displays -> judge it -> assert overall >= 3.5
```

---

## The rubric

Each card is scored 1-5 on four dimensions (full detail in [`rubric.md`](rubric.md)):

- **prompt_fidelity** - did it match the occasion, recipient, and tone asked for?
- **text_accuracy** - grammar, spelling, no hallucinated names or facts
- **style_consistency** - does the tone hold from first line to last?
- **aesthetic** - is the length/shape right for a physical card?

`overall` = average of the four. The judge also returns one line of `reasoning`.

---

## Running it

### Mock mode (no API key, free, deterministic)

Mock mode returns canned cards and fixed scores so you can run the whole
pipeline — and the Playwright test — without any model access. This is the
default when no key is set, and what CI uses.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python run_eval.py --baseline   # save a baseline
python run_eval.py              # run again
python compare.py               # compare latest run to baseline
```

### Real mode (via an OpenAI-compatible gateway)

```bash
cp .env.example .env
# edit .env: set OPENAI_API_BASE, OPENAI_API_KEY, MODEL_NAME, MOCK=0
python run_eval.py --baseline
```

`.env` is gitignored and never committed.

### Playwright e2e + eval test

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
pytest e2e/ -v
```

The test generates a card, renders it in `web/card.html` in a real Chromium
browser, asserts the text displays correctly, then runs the eval judge on the
rendered text and asserts it clears the quality threshold. One test covers both
**"does it render?"** and **"is it good?"**.

---

## Sample report

Real run, judged by `gpt-4.1-mini` against the rubric (`average_overall: 5.0`):

| id | prompt | overall |
|----|--------|--------:|
| birthday-coworker | birthday card for a coworker, warm but professional | 5.0 |
| anniversary-spouse | anniversary card for my wife, romantic and heartfelt | 5.0 |
| graduation-friend | graduation card for a close friend, celebratory and proud | 5.0 |
| getwell-grandparent | get-well card for my grandmother, gentle and caring | 5.0 |
| sympathy-coworker | sympathy card for a coworker, compassionate and respectful | 5.0 |
| valentine-partner | Valentine's card for my partner, affectionate and playful | 5.0 |

*(12 prompts total; six shown.)*

---

## Validating the judge (why the 5.0s are trustworthy)

A common failure of LLM-as-judge setups is **leniency** — the judge rates
everything highly, so the scores mean nothing. The uniform 5.0s above raised
exactly that question.

To check, the judge was fed a deliberately bad card — salesy birthday spam in
response to a *sympathy* prompt. It scored **1.0 across all four dimensions**,
with the reasoning *"completely unrelated spam/gibberish."*

So the judge **discriminates**: good output scores 5.0, bad output scores 1.0.
The high baseline scores reflect that `gpt-4.1-mini` genuinely writes good short
cards — not a broken judge. Validating discrimination with known-bad input is a
core practice for trusting any eval.

---

## Stack

Python 3.12 · LangChain (`ChatOpenAI`, structured output) · Pydantic
(scoring schema) · Playwright + pytest (e2e) · OpenAI-compatible model gateway.
