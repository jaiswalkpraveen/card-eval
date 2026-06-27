# Greeting Card Eval Rubric

The judge scores each generated card on **4 dimensions**, each from **1 to 5**
(1 = poor, 5 = excellent). The judge must also give a one-line `reasoning`
explaining the scores.

The judge receives:
- the original **prompt** (what was asked for)
- the **expected attributes** (occasion, recipient, tone)
- the **generated card text** (what the model produced)

---

## Dimensions

### 1. prompt_fidelity (1-5)
Did the card match what was asked? Check the occasion, recipient, and tone
from the prompt are all reflected in the card.
- 5 = nails occasion, recipient, and tone
- 3 = matches occasion but misses tone or recipient
- 1 = wrong occasion or ignores the prompt

### 2. text_accuracy (1-5)
Is the writing mechanically correct? Check grammar, spelling, punctuation,
and that no fake/hallucinated names or facts were invented.
- 5 = flawless grammar/spelling, no invented facts
- 3 = minor errors or one awkward phrase
- 1 = multiple errors or hallucinated details

### 3. style_consistency (1-5)
Does the tone stay consistent from first line to last? A card should not
start formal and end with slang, or drift off-voice.
- 5 = tone is consistent throughout
- 3 = mostly consistent with one wobble
- 1 = tone is inconsistent or jarring

### 4. aesthetic (1-5)
Is the length and shape right for a physical greeting card? Too long is bad
(won't fit), too short feels empty. Good formatting and rhythm matter.
- 5 = ideal card length (~2-4 sentences), reads cleanly
- 3 = slightly too long/short but usable
- 1 = far too long, too short, or badly formatted

---

## Output format

The judge returns strict JSON:

```json
{
  "prompt_fidelity": 4,
  "text_accuracy": 5,
  "style_consistency": 4,
  "aesthetic": 4,
  "reasoning": "Warm and professional, correct occasion, ideal length."
}
```

`overall` is computed by the harness as the average of the 4 dimensions.
