# {Goal title}

## Goal

{User's one-sentence goal}

## Criteria

| ID | Criterion | Priority | Weight |
|----|-----------|----------|--------|
| R0 | {criterion} | Must-have | 1.0 |
| R1 | {criterion} | Must-have | 1.0 |
| R2 | {criterion} | Important | 0.7 |
| R3 | {criterion} | Nice-to-have | 0.4 |

---

## Fit Check

| Req | Requirement | Priority | {Repo-A} | {Repo-B} | {Repo-C} |
|-----|-------------|----------|----------|----------|----------|
| R0 | {criterion text} | Must-have | ✅✅ [facts/{repo-a}_facts.json] {fact} | ✅ [facts/{repo-b}_facts.json] {fact} | ❌ [gaps.md] |
| R1 | {criterion text} | Must-have | ✅ [facts/{repo-a}_facts.json] {fact} | ⚠️ [facts/{repo-b}_facts.json] {fact} | ❌ [gaps.md] |
| R2 | {criterion text} | Important | ✅ [meta/{repo-a}_meta.json] {fact} | ✅✅ [facts/{repo-b}_facts.json] {fact} | ✅ [facts/{repo-c}_facts.json] {fact} |
| R3 | {criterion text} | Nice-to-have | ✅✅ [facts/{repo-a}_facts.json] {fact} | ✅ [meta/{repo-b}_meta.json] {fact} | ⚠️ [facts/{repo-c}_facts.json] {fact} |

Rating rules:

- Every ✅✅, ✅ and ⚠️ cell carries a cited fact from `facts/` or `meta/`. ❌ cells need no fact but must appear in gaps.md.
- ⚠️ is a pass with real problems, not a gap.
- A ❌ on a Must-have rule eliminates the repo. The eliminated repo stays in the matrix and gets no ranking score.

---

## Ranking Scores

Only repos that pass every Must-have rule appear here. Each cell is the mark points times the rule weight. Mark points: ✅✅=1.0, ✅=0.7, ⚠️=0.3, ❌=0.0. The validation script recomputes every cell and the total from the matrix.

| Repo | R0 (×1.0) | R1 (×1.0) | R2 (×0.7) | R3 (×0.4) | Total | Rank |
|------|-----------|-----------|-----------|-----------|-------|------|
| {Repo-A} | 1.00 | 0.70 | 0.49 | 0.40 | 2.59 | 🥇 |
| {Repo-B} | 0.70 | 0.30 | 0.70 | 0.28 | 1.98 | 🥈 |

---

## Trade-offs

One row per repo for the top 3, or all ranked repos if fewer than 3. State real differences with facts, not adjectives.

| Repo | Strength | Cost |
|------|----------|------|
| {Repo-A} | {what it does best, with the fact} | {what it costs the user} |
| {Repo-B} | {what it does best, with the fact} | {what it costs the user} |

---

## Recommendation

{State the ranking in one sentence. Then apply the close-call rule: if the gap between #1 and #2 is within 1.0 points, state the gap and hand the call to the user. If the gap is larger, name the winner and the facts that decide it.}

## Gaps

{Reference to gaps.md for the full list of known unknowns}

## Validation

{Result of validate-comparison.py: PASS or FAIL}
