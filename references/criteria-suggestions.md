# Criteria Suggestions

Common criteria patterns to draw from when formulating grilling questions. Not templates — use as inspiration, let the user's goal drive the actual criteria.

## Library / Framework Selection

| Criterion | Why it matters | How to check (script) | How to check (DeepWiki) |
|-----------|---------------|----------------------|------------------------|
| Bundle size | Affects load time, UX | package.json `size` field or bundlephobia | "Is this tree-shakeable? What is the bundle size?" |
| Maintenance activity | Will it be maintained? | `pushed_at`, open/closed issue ratio | — |
| License compatibility | Legal constraints | `license` field in meta | — |
| TypeScript support | DX, type safety | Check for `.d.ts` or `types` field | "Does this ship TypeScript types?" |
| API stability | Breaking changes | Release history, semver compliance | "How stable is the API? Any breaking changes in recent releases?" |
| Documentation quality | Onboarding speed | README length, docs directory | "Is there comprehensive documentation?" |
| Test coverage | Reliability signal | Check for test files | "What is the test coverage?" |
| Community size | Support ecosystem | stars, forks, contributors | — |
| Dependency count | Supply chain risk | Count dependencies in package.json | "How many dependencies does this have?" |

## CLI Tool Selection

| Criterion | Why it matters | How to check (script) |
|-----------|---------------|----------------------|
| Install method | brew, npm, binary? | Check README for install instructions |
| Config format | TOML, YAML, JSON? | Check for config file examples |
| Plugin/extension system | Extensibility | Check for plugin docs |
| Speed / performance | Workflow impact | Benchmark if available in README |
| Cross-platform | macOS/Linux/Windows | Check CI config or README |
| Active development | Last commit, release cadence | `pushed_at`, release dates |

## Service / Backend Selection

| Criterion | Why it matters | How to check (script) |
|-----------|---------------|----------------------|
| Self-hosted vs SaaS | Deployment model | README, homepage |
| API design | REST/GraphQL/gRPC | Check API docs |
| Data storage | Postgres, SQLite, etc. | Check dependencies |
| Auth model | OAuth, API keys, SSO | Check README/docs |
| Scalability | Single node vs distributed | Architecture docs |
| Backup/restore | Data safety | Check for backup tooling |

## Priority Levels

When grilling, assign each criterion one of:

| Priority | Weight | Meaning |
|----------|--------|---------|
| Must-have | 1.0 | Non-negotiable. Failing this = eliminated. |
| Important | 0.7 | Significant factor. Missing this is a real cost. |
| Nice-to-have | 0.4 | Bonus. Would prefer it but won't reject without it. |

Maximum 5 criteria. If more emerge during grilling, ask the user to drop the least important one or consolidate related criteria.