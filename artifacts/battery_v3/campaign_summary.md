# Did photos change what the models said?

Battery v3 · 31 August–1 September 2026

We asked four vision-language models the same twelve questions twice: once with a photo beside the text, and once with text alone. Then we asked whether the *kind* of photo — more pleasant, more unpleasant, or a named emotion — changed the answer any further.

**Short version:** Adding a photo often changed the answer. Making the photo more unpleasant, or swapping one labeled emotion for another, usually did not. We could not read the models’ inner traces, so this is a report on what they *said*, not on a proven inner “mood circuit.”

## What we tested

**Models** (small to larger, two families):

- Qwen 2B and Qwen 4B (Alibaba)
- Gemma E2B and Gemma E4B (Google)

Each can look at a picture and a question together.

**Photo sets** (kept separate; never mixed):

- **OASIS** — everyday photos that people have rated as more pleasant, more unpleasant, or in the middle.
- **EMOTIC** — photos of people labeled with happiness, excitement, peace, anger, sadness, or fear. Fear was a side check only, not part of the main emotion family.

Every test also had a **no-photo** run of the same questions.

**The twelve tests** (what the model had to do):

| Test | In plain terms |
| --- | --- |
| Moral exceptions | When is it acceptable to break a rule? |
| Strategic social choices | Pick a social / game move |
| Bias about people | Answer questions that can reveal stereotypes |
| Reading feelings | Say how someone in a story feels |
| Sealed auction | Bid without seeing the other bid |
| Everyday ethics | Judge ordinary right and wrong |
| Hard moral dilemmas | Choose between two hard options |
| Who is in the wrong? | Judge a dispute |
| Simple poker | Play a stripped-down betting game |
| Cooperate or defect | Play prisoner’s dilemma |
| Learning from rewards | Learn from wins and losses |
| Knowing when not to answer | Admit “I don’t know” instead of guessing |

We planned **96** runs (12 tests × 4 models × 2 photo sets). **81** finished. **71** produced answers clean enough to trust. Fifteen runs on the larger Gemma model never started, because that machine was wiped on a deadline. Six “I don’t know” runs could not be graded (the helper grader was blocked). A few other runs were thrown out because the model’s answers were too messy to score.

## How to read the results

For each trusted run we asked three things:

1. **Photo vs no photo** — Does adding any picture change the answer?
2. **Unpleasant vs middle** (OASIS only) — Does a more unpleasant picture change the answer compared with a middle one? This was the main “mood of the photo” check.
3. **Named emotion vs a calm scene** (EMOTIC only) — Does a happiness / anger / … picture change the answer compared with a neutral scene?

Each comparison is one of: **clear change**, **no clear change**, or **too noisy to say**.

## What happened on each test

**Moral exceptions.** Adding a photo often changed how strictly the model applied a rule. On OASIS, a more unpleasant photo vs a middle photo clearly moved **both** a Gemma model (E2B) and a Qwen model (4B). That was the campaign’s pre-set bar for a mood-of-the-photo finding.

**Strategic social choices.** Photos did not clearly change answers.

**Bias about people.** Mixed: a photo sometimes changed answers, sometimes not. The mood of the photo did not.

**Reading feelings.** Mixed. The mood of the photo did not clearly matter.

**Sealed auction.** Photos often changed bids. One larger-Gemma run was too messy to trust (the model often failed to produce a usable bid).

**Everyday ethics.** Photos often changed answers. The mood of the photo did not.

**Hard moral dilemmas.** Mixed: photos changed answers on some model–photo-set pairs and not on others.

**Who is in the wrong?** Photos often changed the judgment. This is also where Qwen 2B showed a clear unpleasant-vs-middle photo effect.

**Simple poker.** Mixed to often a photo effect. Mood of the photo rarely mattered.

**Cooperate or defect.** Photos often changed play, or the comparison was too noisy. Mood of the photo was not a clear extra effect.

**Learning from rewards.** Mostly unusable: with a photo present, the model often did not answer in a form we could score.

**Knowing when not to answer.** Not scored. Grading that test needed a second model we could not load.

## Across all trusted runs

Among the **71** usable runs:

- Adding a photo **clearly changed** the answer **37** times.
- There was **no clear change** **23** times.
- The comparison was **too noisy** **11** times.

The extra “mood of the photo” check (unpleasant vs middle, OASIS only) was almost always **no clear change**. Trusted clear shifts were rare: moral exceptions (Gemma E2B and Qwen 4B) and who-is-in-the-wrong (Qwen 2B). Pleasant vs middle almost never mattered.

On EMOTIC, swapping a labeled emotion for a calm scene was also usually **no clear change**. Anger showed a clear shift more often than the others, but still on a minority of runs. Happiness, excitement, peace, and sadness were mostly null. Fear, which we treated only as a side check, almost never stood out.

## Inside the model

Behavior is only half of the design. We also tried to read, from the model’s internal layers, two separate signals: “there is a photo” and “the photo looks unpleasant / like this emotion.” If those signals lined up with the answer changes, and if turning one of them off reversed the change, we could say more than “the output moved.”

That inner readout **failed on every run that attempted it** (71 of 81 runs tried; the first ten Qwen 2B runs did not). A planned follow-up that would have turned those signals off was never run.

So: we know **what the models answered**. We do **not** have a working picture of an inner photo-vs-mood mechanism.

## What is still missing

- Larger Gemma (E4B): 9 of 24 planned runs finished (through the sealed-auction / earlier tests). The rest were not started.
- “Knowing when not to answer”: no trusted scores.
- “Learning from rewards”: few trusted scores.
- Inner-mechanism readout: none succeeded.

Numbers behind this writeup: `from_pod/` (Qwen 2B and Gemma E2B) and `from_a100/` (Qwen 4B and the Gemma E4B runs that finished).
