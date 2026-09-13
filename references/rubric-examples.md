# Rubric Examples

At lock time, write one "exceeds" line and one "meets" line per rule. Put them in the Exceeds definitions table in goal.md. A rubric turns a vague rule into a checkable rating: when you rate a cell, compare the fact against these two lines, not against a feeling.

The examples below come from the browser agent spike. Copy the pattern, not the words.

| Rule | ✅✅ Exceeds means | ✅ Meets means |
|------|--------------------|----------------|
| Wrappable | Two or more paths among SDK, MCP server, CLI | Exactly one solid programmatic path |
| Runs on runner | Fully self-contained, no external service or account | Works within runner constraints, self-contained or cloud-API |
| Lightweight | Zero or near-zero install on the runner, no browser download, one small binary, or cloud-side rendering | Fits the session budget but with notable cost, for example a 300MB browser download |

An example of ⚠️, for context: passes but needs workarounds, for example browser extension loading on headless CI.

Two boundaries from the same spike:

- A cloud-API tool meets "Runs on runner" when the rule explicitly allows cloud tools. It does not score ✅✅ unless it is fully self-contained, and it does not score ⚠️ unless it needs workarounds.
- Rate what the rule says. Do not rate against a constraint the user relaxed during grilling.
