# Changelog

## 0.2.0 — 2026-09-19
- Self-evolution is now reviewed by an INDEPENDENT external reviewer, not by
  devcrew itself: a GitHub Action (.github/workflows/framework-review.yml) runs
  a Bedrock model from a different family on every PR touching framework/, hosts/,
  or AGENTS.md, checks it against the design invariants, and posts a verdict.
- devcrew NEVER pushes main or self-merges framework changes; the CEO merges.
- Added docs/self-evolution-review.md (flow + one-time GitHub/OIDC/branch-protection setup).

## 0.1.0 — 2026-09-19
- Initial devcrew AIDLC team: orchestrator + 7 role agents (Architect, Design,
  Frontend, Backend, QA, Security, DevOps).
- AIDLC collaboration protocol (phases, gates, contract hand-offs, adversarial
  decision points, gated self-evolution).
- Host-neutral source under framework/ with KiroCrew and Claude Code adapters.
- Shared team memory (lessons, ADRs, retrospectives).
- AI-bootstrap install via AGENTS.md (no human-run installer).
