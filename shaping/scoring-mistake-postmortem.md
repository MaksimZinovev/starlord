# Starlord — Scoring Mistake Post-Mortem & Recommendations

## What happened

During the Browser Agent Spike, Cloudflare Browser Run was scored ⚠️ (partial) on R1 ("Runs on GitHub Actions runner — Both self-contained and cloud-API tools are acceptable"). The criterion explicitly says cloud-API tools are acceptable. Cloudflare is a cloud-API tool. It should have scored ✅✅ (exceeds). I smuggled the R8.1 "no external server" constraint — which was deliberately relaxed during grilling — back into the scoring through the back door. The documents, criteria, and facts were all correct. The mistake was in the scoring step: I let a relaxed constraint override the explicit criterion text.

## User's question

> ok, note what just happened, step back and think about it from process perspective - although the documents, criteria and facts were there you made a mistake in scoring - suggest 3 ideas, use AI agentic engineering design patterns to mitigate or avoid this in the future?

## Recommendations

1. **Validator agent**: separate pass re-reads each score against the criterion text, flags contradictions.
2. **Conformance gate**: automated check — "does any rating violate what the criterion explicitly allows?"
3. **Self-critique loop**: before finalizing, agent asks "did I smuggle in a relaxed constraint?"
