# Self-evolution review — how it works & one-time setup

Every change to devcrew's own definition (`framework/**`, `hosts/**`,
`AGENTS.md`) is reviewed by an **independent reviewer outside devcrew**, so the
framework cannot bias its own evolution. The reviewer runs on **AWS Bedrock**
(free against your own token budget), via a free GitHub Action, and **never
merges** — the CEO does.

## Flow

```
devcrew drafts a framework change
   → opens a PR (never pushes main, never self-merges)
   → GitHub Action `framework-review` runs on PR
   → Bedrock model (different family from devcrew) reviews the diff vs the
     design invariants → posts APPROVE / REQUEST-CHANGES / REJECT
   → branch protection blocks main until the check passes
   → CEO reads the verdict and merges
```

## One-time GitHub setup (public repo — all free)

1. **Push the repo** to `github.com/shazi7804/devcrew` and set it **Public**.

2. **AWS OIDC role for the Action** (no long-lived keys in GitHub):
   - Create an IAM role trusting GitHub's OIDC provider
     (`token.actions.githubusercontent.com`), scoped to
     `repo:shazi7804/devcrew:*`.
   - Attach a policy allowing `bedrock:InvokeModel` on the review model only.
   - Repo → Settings → Secrets and variables → Actions:
     - **Secret** `AWS_REVIEW_ROLE_ARN` = the role ARN.
     - **Variable** `AWS_REVIEW_REGION` = e.g. `us-east-1`.
     - **Variable** `BEDROCK_REVIEW_MODEL_ID` = a model from a DIFFERENT family
       than the devcrew agents run on (that difference is the point). Pick a
       current Bedrock model id at setup time.

3. **Branch protection** on `main` (Settings → Branches → Add rule):
   - Require a pull request before merging.
   - Require status checks to pass → select **framework-review**.
   - (Optional) Include administrators, so even you cannot bypass the gate.

That is the whole gate: devcrew opens PRs, Bedrock reviews them for free, `main`
stays protected, and you merge.

## Why external, not a devcrew role

A `devcrew-reviewer` agent would share the same model family, the same skill
conventions, and the same `framework/memory/` — it would be biased toward
approving its own team's changes. Moving the reviewer OUT of devcrew (a
different Bedrock model, no devcrew memory, running in CI) is what makes the
review independent.
