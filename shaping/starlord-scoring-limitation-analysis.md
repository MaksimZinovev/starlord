# Starlord Scoring Method — Limitation Analysis

> Context: Browser Agent Spike (C2.4, R8.2). Cloudflare Browser Run scored 3.8 — same as Playwright — despite being dramatically lighter. This document explains why and recommends a scoring improvement.

---

## Why the score is identical (3.8 = 3.8)

The starlord scoring formula is:

```
score = Σ (priority_weight × {✅=1, ❌=0})
```

This is **purely binary** — a criterion either passes or fails. There's no notion of *how well* it passes. Both Playwright and Cloudflare Browser Run pass all 5 criteria, so they both get the maximum possible score (3.8). The formula literally cannot produce a different number.

Here's the specific problem with R3 (Lightweight):

| | Playwright | Cloudflare Browser Run |
|---|---|---|
| Browser download | 300MB+ Chromium | 0 MB |
| System deps | `playwright install --with-deps` | None |
| Setup time | `npm ci` + browser install | Single `curl`/`fetch()` |
| R3 score | ✅ = **0.7** | ✅ = **0.7** |

Cloudflare is *dramatically* lighter — arguably the lightest option in the entire comparison — but the binary scoring treats "barely lightweight enough" and "zero-weight" as identical. Both are ✅, both get 0.7.

## Three things the scoring method can't capture

**1. Quality of pass (graduated vs binary)**

The binary ✅/❌ loses all quality information within the passing set. A tool that *barely* meets a criterion gets the same score as one that *exceeds* it. This is fine for filtering (eliminating tools that don't meet criteria at all), but useless for *ranking* among tools that all pass.

**2. No penalty for external dependencies**

R8.1 ("no external server") from the shaping doc isn't one of the 5 locked criteria — the user's grilling explicitly relaxed it to "evaluate both." So the external dependency concern has *nowhere to land* in the score. It's noted in the qualitative analysis ("⚠️ External service") but doesn't affect the number. There's no mechanism for "this passes all criteria but has a structural concern."

**3. No cross-criterion trade-off awareness**

The score is a simple sum. It can't capture that Cloudflare's extreme lightness (R3) *compensates* for its external dependency (which isn't even a criterion), or that Playwright's self-containment (no external service) *compensates* for its heavier install. These trade-offs are real but invisible to addition.

## Should starlord's scoring change?

I'd recommend a **two-phase scoring** approach — keep binary for filtering, add graduated for ranking:

### Phase 1: Binary filtering (unchanged)

The current `✅=1, ❌=0` system is good for what it does: narrowing 131 candidates to 15 by eliminating tools that fail must-have criteria. It's fast, unambiguous, and works well for the funnel. Don't change this.

### Phase 2: Graduated ranking for the top tier (new)

For candidates that pass all must-haves (the tied top tier), switch to a **3-level scale** per criterion:

| Level | Symbol | Multiplier | Meaning |
|-------|--------|------------|---------|
| Exceeds | ✅✅ | ×1.0 | Significantly better than "meets" — a standout strength |
| Meets | ✅ | ×0.7 | Satisfies the criterion adequately |
| Partial | ⚠️ | ×0.3 | Technically passes but with notable caveats |
| Fails | ❌ | ×0.0 | Does not meet |

Applied to the Playwright vs Cloudflare comparison:

| Req | Weight | Playwright | Cloudflare Browser Run |
|-----|--------|------------|------------------------|
| R0 Wrappable | 1.0 | ✅✅ (1.0) — SDK + MCP + CLI | ✅✅ (1.0) — REST + MCP + CDP + Puppeteer |
| R1 GH Actions | 1.0 | ✅✅ (1.0) — runs locally, zero external deps | ⚠️ (0.3) — runs on Cloudflare edge, external dependency |
| R2 Maintenance | 0.7 | ✅ (0.49) — actively maintained | ✅ (0.49) — actively maintained |
| R3 Lightweight | 0.7 | ✅ (0.49) — 300MB+ browser download | ✅✅ (0.7) — zero browser download, lightest possible |
| R4 TS/JS native | 0.4 | ✅✅ (0.4) — pure TypeScript | ✅ (0.28) — TS-compatible but browser is remote |
| **Total** | | **3.38** | **2.77** |

Now the scores differentiate: Playwright scores higher because its self-containment (R1 = exceeds, no external dependency) is weighted as a must-have (×1.0), while Cloudflare's extreme lightness (R3 = exceeds) is only weighted as important (×0.7). The must-have weight on R1 properly reflects that "runs on the runner without external infrastructure" matters more than "how light is the install."

### What NOT to change

- **Keep 5 criteria max.** The constraint forces focus. Adding criteria to capture every nuance would dilute the signal.
- **Keep binary for Phase 1.** Graduated scoring on 131 candidates would be expensive and noisy. Binary filtering is the right tool for the funnel.
- **Keep the qualitative analysis section.** The "Score False Positives" and "Trade-offs" sections in comparison.md already do the work that graduated scoring formalizes. The scoring change would just make the numbers reflect what the prose already says.

### Deliberate choice

"no external dependency"was a deliberate decision to keep options open, and the  
 graduated scoring is designed to honor exactly that. The framing was wrong: the relaxation
 isn't a problem to fix, it's a choice the scoring should respect while still showing you the  
 quality difference so you can make the trade-off call yourself. Phase 2 graduated scoring
 doesn't say "Cloudflare should have been filtered out" — it says "both pass, but here's how
 well each passes, so you can weigh the trade-off you deliberately opted into."

So there are two valid responses:

1. **Change the scoring** (graduated Phase 2) to differentiate quality within the passing set — this is what I recommend.
2. **Tighten the criteria** (restore "no external service" as a must-have) — this would have filtered Cloudflare out entirely, but the user explicitly chose to evaluate it.

The graduated approach is better because it preserves the user's "evaluate both" decision while still producing a ranking that reflects the trade-offs.
