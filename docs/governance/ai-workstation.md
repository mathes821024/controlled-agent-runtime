# AI workstation

**Status:** operating agreement for this repository. Not a product Gate PASS, and not permission to deploy or execute real actions.

People manage project state. Models are not workstations.

## Topology

```text
Owner
  → ChatGPT (Mac)
      control, Gate Review, architecture judgment, task split,
      instructions to Grok Bot, retro
  → Mac Cursor
      Design Station
      Product Manager, UX Architect, UI Designer, Backend Architect
  → Mac Grok Bot
      primary engineer
      code, tests, fixes, git, test-environment deploy
  → GitHub
      the only remote source of truth
  → 51.81.146.19
      later Human Acceptance Environment
```

Cursor account B is capacity backup. When account A runs out of quota, switch accounts and continue the same repository and workspace. The account is not a second design station or a second build station.

## Main line

Think → See → Decide → Freeze → Build → Verify.

On this project that maps to:

```text
THINK     Mac Cursor, one role at a time
DECIDE    ChatGPT + Owner
FREEZE    Owner decision, then GitHub
BUILD     Mac Grok Bot
VERIFY    tests, ChatGPT review, Owner
```

## Single writer

One agent holds the write mindset at a time. Other roles may read and recommend. They do not edit the same files in parallel.

`@product-manager`, `@ux-architect`, `@ui-designer`, and `@backend-architect` select a thinking role. They do not grant `edit`, `commit`, `push`, `deploy`, or `production_access`.

## What this does not change

- Owner remains the final Admission, Decision, and Execution Gate in `GOVERNANCE.md`.
- Gate 0 still does not include a production runtime or real execution.
- Naming `51.81.146.19` records the future acceptance host. It does not authorize deployment, and this repository stores no credentials for it.
- Before a public release, confirm this host meets the private-endpoint check in the public-release checklist.
