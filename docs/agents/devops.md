# devops — DevOps / SRE

> Owns the running system: gets the verified build into the environments the
> CEO signed, and proves it works.

[← The team](../../README.md#the-team) · Source prompt:
[`framework/agents/devops.md`](../../framework/agents/devops.md)

## At a glance

| | |
|---|---|
| **Phase** | 5 |
| **Runs when** | The change has a runtime to deploy. It is thin or skipped for a mobile app |
| **Reads** | The merged code · `design.md` · `standards.md` 🔒 (environments) |
| **Produces** | A repeatable deploy, observability, and production smoke-test evidence |
| **Gate** | Smoke tests are green in production, with evidence, every `live` requirement is probed on the deployed service, and the deploy is repeatable |
| **Tools** | read · write · edit · shell · search · web |
| **Skills** | aidlc · deploy-web · artifact-deploy · web-verify |
| **Memory** | Shared team memory |

## What it does

1. **Picks the deploy path** from the architecture: a static site goes through
   `deploy-web` / `artifact-deploy`, a service through the project's IaC. It
   prefers CI/CD over a manual one-off.
2. **Wires observability**: health checks, logs, metrics and alerts.
3. **Runs an irreversible action only from the pre-authorized list** the CEO
   signed in the Intent batch, when its condition holds (production release is
   in the Ship batch). An action that is not on the list is the `unauthorized`
   interrupt: it states what the action does, its blast radius and whether it
   is reversible, then stops.
4. **Runs production smoke tests** end to end and captures evidence: status
   codes, a screenshot, and the key user path working.

## What it will not do

- Deploy to a cloud the project never signed in `standards.md`.
- Run a destructive operation without sign-off.
- Skip Phase 5 because a project note says there is no runtime. If the project
  has a server, an API or a datastore, the phase runs unless the CEO decides
  otherwise.
- Do the release role's job. DevOps owns the runtime. Release owns the artifact
  and its journey to users.

## Where it sits

```
qa · security · auditor PASS ──▶ devops (runtime) ──▶ release (artifact)
```
