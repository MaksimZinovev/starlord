# {Goal title}

## Goal

{User's one-sentence goal}

## Criteria

| ID | Criterion | Priority | Weight |
|----|-----------|----------|--------|
| R0 | {criterion} | Must-have | 1.0 |
| R1 | {criterion} | Important | 0.7 |
| R2 | {criterion} | Nice-to-have | 0.4 |

---

## Fit Check

| Req | Requirement | Priority | {Repo-A} | {Repo-B} | {Repo-C} |
|-----|-------------|----------|----------|----------|----------|
| R0 | {criterion text} | Must-have | ✅ [meta/{repo-a}_meta.json] | ❌ | ✅ [facts/{repo-c}_facts.json] |
| R1 | {criterion text} | Important | ✅ [facts/{repo-a}_facts.json] | ✅ [meta/{repo-b}_meta.json] | ❌ [gaps.md] |
| R2 | {criterion text} | Nice-to-have | ✅ [meta/{repo-a}_meta.json] | ✅ [meta/{repo-b}_meta.json] | ✅ [facts/{repo-c}_facts.json] |

---

## Weighted Scores

| Repo | R0 (×1.0) | R1 (×0.7) | R2 (×0.4) | Total | Rank |
|------|-----------|-----------|-----------|-------|------|
| {Repo-A} | 1.0 | 0.7 | 0.4 | 2.1 | 🥇 |
| {Repo-B} | 0.0 | 0.7 | 0.4 | 1.1 | 🥈 |
| {Repo-C} | 1.0 | 0.0 | 0.4 | 1.4 | 🥉 |

---

## Recommendation

{2-3 sentence recommendation based on the scores, highlighting the winner and key tradeoffs}

## Notes

- {Repo-A} fails R{X}: {reason} [source file]
- {Repo-B} ✅ R{X}: {fact} [source file]

---

## Gaps

{Reference to gaps.md for full list of known unknowns}

## Validation

{Result of validate-comparison.py — PASS or FAIL}