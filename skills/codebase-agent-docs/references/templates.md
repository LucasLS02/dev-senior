# Templates

Skeletons for every file in the system. They are stack-agnostic — fill them
from the Phase 1 fact sheet, never from assumption.

Write prose in the project's dominant language (detected in Phase 1). Keep
headings, code, commands and paths as they appear in the repo. The templates
below use English headings; translate them if the project's prose is not
English, and keep the translation consistent across all files.

Placeholders: `<name>` snake singular, `<names>` plural, `<Name>` PascalCase,
`<unit>` the repo's most-repeated code unit.

---

## Root `AGENTS.md`

Ceiling 120 lines. Four tables, three code blocks, one bullet list, almost no
connective prose. **No procedure lives here.**

````markdown
# <Project> — Agent Navigation Guide

## What this product does

<Two to four lines: what it is, what it ingests, what it produces.>

**Does NOT**: <the boundaries — what it never serves, owns, or exposes.>
<One clause naming what it actually is: "X is a sync engine only.">

## Stack

| Layer | Technology |
| --- | --- |
| Runtime | <lang + version> |
| <Framework layer> | <name + version> |
| <Data store> | <name (non-default trait)> |
| Lint/format | <tool (config that differs from default)> |
| Tests | <framework + helpers> |

Parenthesize every non-default choice. `Celery 5.6 (thread pool, not prefork)`
teaches more than `Celery 5.6`.

## Setup & commands

```bash
<setup command>      # <the non-obvious part of this step>
<run command>        # <what it actually starts>
<test command>       # <scope, and what it does not need>
<validate command>   # <what it runs>
```

See [docs/agents/development.md](docs/agents/development.md) for ports, env
vars, and iteration tips.

## Architecture

```text
<dir>/       # <role of this directory>
<dir>/       # <role>
<entry>      # <app factory / main; note if ordering is significant>
```

<The one wiring fact an agent cannot infer, e.g. registration order:>

```text
<ServiceA> → <ServiceB> → <ServiceC>
```

<Its consequence, in one sentence, with the surprising token bolded.>

## Topic index

| File | What it covers |
| --- | --- |
| [docs/agents/workflow.md](docs/agents/workflow.md) | <one line> |
| [docs/agents/gotchas.md](docs/agents/gotchas.md) | Domain invariants and non-obvious traps |
| [docs/agents/dont-touch.md](docs/agents/dont-touch.md) | Generated files, secrets, protected configs |
| [docs/agents/<unit>-anatomy.md](docs/agents/<unit>-anatomy.md) | Canonical <unit> structure |
| [docs/agents/tests.md](docs/agents/tests.md) | <one line> |
| [docs/agents/code-style.md](docs/agents/code-style.md) | <one line> |
| [docs/agents/commits-prs.md](docs/agents/commits-prs.md) | <one line> |
| [docs/agents/development.md](docs/agents/development.md) | <one line> |
| [docs/agents/recipes/<verb>-<noun>.md](docs/agents/recipes/<verb>-<noun>.md) | Walkthrough: <what it produces> |

Recipe rows are prefixed `Walkthrough:` so an agent can tell a reference from a
runbook without opening it.

## Layer guides

- [<dir>/AGENTS.md](<dir>/AGENTS.md) — <what this layer is>
- [<dir>/AGENTS.md](<dir>/AGENTS.md) — <what this layer is>

## Truth sources

| Topic | Authoritative location |
| --- | --- |
| Schema | `<path>` |
| Business rules | `<path>` |
| <State machine> | `<path>` |

Three to seven rows. Point at the file that *defines* the fact, not the file
that describes it.

## Conflict resolution

When this file and the code disagree, **trust the code**. This file describes
intent; the code is ground truth. File a doc fix alongside any code change.
````

---

## Directory `AGENTS.md`

25–75 lines, 3–6 `##` sections. Three jobs only: an inventory of what lives
here, the local naming convention, and the one or two traps specific to this
directory.

Never repeat from the root: stack, setup commands, product description, topic
index, truth sources, conflict resolution. Never link sideways to another
directory guide. Heading names must not collide with the root's.

````markdown
# <dir>/ — <Role>

<Optional one-paragraph preamble. Allowed here; not at the root.>

## <Inventory heading — "Layers" / "Service catalog" / "Modules">

| <Thing> | <One clause each> |
| --- | --- |
| `<name>` | <what it is, disambiguated from its neighbours> |

## <Local naming convention>

<The pattern, then one real example of a correct name.>

## <The local trap>

<Mechanism → consequence → imperative. Bold the surprising token.>

See [docs/agents/<file>.md](../docs/agents/<file>.md) for the full walkthrough.
````

Link out only for a procedure this file refuses to inline. Use relative paths.

---

## `workflow.md`

40–50 lines. The rules an agent must obey before touching anything.

````markdown
# Workflow — <Model Strategy & Work Rules>

## Model strategy

- <task kind> → <model>, <effort level>
- <task kind> → <model>

## Work rules

1. Read the relevant source files before making any claim about the code.
1. <rule>
1. <rule — never commit without approval>
1. <rule — never push, merge, or rewrite history without approval>
1. <project-specific rules last>

Numbered imperatives, one situation each. Under 6 rules and agents miss edge
cases; over 20 and they stop reading carefully. Every item written `1.`.

## <Pipeline mental model>

```text
<ASCII of the runtime data flow, if the project has one>
```
````

---

## `gotchas.md`

Up to ~140 lines, one `##` per trap, ~6 lines each, no intro, no `###`.

Three beats per entry, fixed order: **mechanism → silent consequence →
imperative correction.**

````markdown
# Gotchas — Domain Invariants & Traps

## <Assertive claim, or `X, not Y`>

<The mechanism, naming the exact symbol.> <The consequence — say plainly that
it fails silently, with no warning, if that is true.> <The correction: "Never
X." / "Use Y instead.">

## `<symbol>` is <surprising property>

<Same three beats.>
````

Heading styles that work, in order of density:

| Style | Example |
|---|---|
| Contrastive rule | `## UUID v7, not UUID v4` |
| Property assertion | `` ## `auth_data` is encrypted `` |
| Behaviour surprise | `` ## `make run` always rebuilds `` |
| Symbol vs symbol | `` ## `a.field` vs `b.field` `` |

The heading set should read as a scannable table of contents of dangers.
Append new traps at the bottom of their rough group.

Admission test: a reasonable senior developer would get this wrong, **and** the
failure is quiet. Loud failures teach themselves.

---

## `dont-touch.md`

~45 lines, effectively all tables. Categorize by **why hands off**, not by file
type — the verdict goes in the heading, the reason goes in a column.

````markdown
# Don't Touch — Protected Files & Access Rules

## Generated files — never hand-edit

| File | Generator | Rule |
| --- | --- | --- |
| `<path>` | `<command>` | <rule + how to regenerate> |

## Secret / credential files — never commit

| File | Purpose |
| --- | --- |
| `<path>` | <what it holds> |

These files are in `.gitignore`. Never commit them. Never log their contents.

## Protected config — change with care

| File | Risk |
| --- | --- |
| `<path>` | <what breaks> |

## Manually-maintained critical files

| File | Why it's critical |
| --- | --- |
| `<path>` | <what silently breaks if it drifts out of sync> |
````

The fourth category is the one most projects miss: files you **must** remember
to update. A file can legitimately appear in two categories.

---

## `<unit>-anatomy.md`

~140 lines. The highest-leverage file to port: every codebase has a repeated
unit worth templating — a domain module, a React feature folder, a Go package,
a Rails resource, a Terraform module. Name the file after that unit.

Four devices, in this order:

````markdown
# <Unit> Anatomy

Every <unit> under `<path>/<name>/` has this exact internal layout. Do not
deviate from this structure.

```text
<path>/<name>/
  <file>        # <role> (<base class / contract it implements>)
  <file>        # <role>
  tests/
    <pattern>   # <what these cover>
```

## <file>

```<lang>
<minimal compilable skeleton, real imports, `...` for elided bodies,
 inline comments carrying rationale>
```

Rules:

- <what the snippet cannot show>
- <a boundary: what must never appear in this file>
````

The annotated tree replaces a file-roles table. Give a `Rules:` list only to
the non-trivial files; for the trivial ones the naming pattern *is* the rule.

Never put a checklist or an ordered procedure here — this file describes the
target state. The procedure belongs in a recipe.

---

## `tests.md`

~100 lines. Taxonomy first, judgement calls last.

````markdown
# Tests — <Stack, Factories, Coverage>

## Test types

| Type | File pattern | Needs | Runs with |
| --- | --- | --- | --- |
| Unit | `<pattern>` | <deps> | `<command>` |
| Integration | `<pattern>` | <deps> | `<command>` |

<The one sentence the table cannot express — e.g. how a suite is selected.>

## <Fixtures / factories>

<The project's idiom, with a real snippet and a pointer to a real exemplar
file: "See `<real_test_file>` for the established pattern.">

## Coverage

<Target, and how it is measured.>

## Writing tests

1. <what to assert on>
1. <what NOT to test — naming the framework behaviour that is out of scope>

## <Learned lesson>

<Gotcha-shaped prose. This file legitimately accretes field lessons at the
bottom; keep them as flat `##` sections.>
````

---

## `code-style.md`

~50 lines.

````markdown
# Code Style

## Linter / formatter

<Tool, config path, the settings that differ from default, the command.>

## Language

<Which language for identifiers, which for prose and commit messages. State it
explicitly — mixed-language projects create drift.>

## Naming conventions

| Thing | Convention | Example |
| --- | --- | --- |
| <kind> | <rule> | `<real example from the repo>` |

## Design principles

1. <principle, as an imperative>
1. <principle>

## Comment policy

<When a comment is required, and when it is noise.>
````

---

## `commits-prs.md`

~50 lines, ending in a checklist.

````markdown
# Commits & PRs

## <Commit convention>

| Type | Use for |
| --- | --- |
| `feat` | <…> |
| `fix` | <…> |

```text
<three to five real commit subjects harvested from this repo's history>
```

## Branch naming

<Pattern + one real example.>

## Pre-commit hooks

<What runs. Then: do not bypass with `--no-verify` — fix the issue instead.>

## PR checklist

- [ ] `<validate command>` passes
- [ ] `<test command>` passes
- [ ] New <unit> follows the anatomy doc
- [ ] <project-specific gate>
````

Harvest the commit examples from `git log`. Invented examples teach invented
conventions.

---

## `development.md`

~75 lines. Alternating copy-pasteable command blocks and two-column tables.
Shrinks to a few lines when everything is standard — that is a success, not a
gap.

````markdown
# Development — Setup, Ports, Env Vars

## Initial setup

```bash
<commands, each with the non-obvious part as an inline comment>
```

## <Non-standard ports>

| Service | Port | Notes |
| --- | --- | --- |
| <name> | **<port>** | Not <the default anyone would assume> |

Include this section only if a port differs from its default. Bold the number.

## Key environment variables

| Variable | Purpose |
| --- | --- |
| `<VAR>` | <what breaks without it> |

## Faster iteration

<How to avoid the slow default path.>

## Adding dependencies

```bash
<the exact commands, per dependency group>
```
````

---

## Subsystem topic file

Create one per subsystem an agent will get wrong from reading the code alone —
auth, deployment, background jobs, state management, a gnarly third-party
integration. The rule of admission: **it has bitten someone twice.**

````markdown
# <Subsystem> — <the three things covered>

## Stack

<One paragraph: the moving parts and how they connect.>

## <Flow>

1. <step in the runtime sequence>
1. <step>

## <How to declare / use it in code>

```<lang>
<the smallest real example>
```

## <Behaviour in tests>

<Whether it is disabled, mocked, or real — and the trap if assumed otherwise.>

## <Accounts / profiles / caches>

| <Thing> | <Value> |
| --- | --- |
````

---

## Recipe

60–160 lines, 6–13 steps. Runbook, not reference.

````markdown
# Recipe: <Imperative action>

<Optional single framing line: "Follow these steps in order. Each step is an
action.">

## Prerequisites

- <required state, e.g. the stack is running>
- <required prior step>

## 1. <Imperative verb phrase>

```bash
<copy-pasteable command, including env setup, repeated in full — no "see above">
```

<One to three lines stating the rule or the why. Prose after code, never
before, unless the step needs a locator: "Open `<file>` and add:">

## 2. <Imperative verb phrase>

```<lang>
<skeletal snippet: full imports, `<name>` placeholders, `...` where the real
 work goes>
```

<Inline the failure mode at the point of failure, bolded:
 "Without this, <tool> **will not detect** the new <thing>.">

## <n>. Run validation

```bash
<validate command>
<test command>
```

## <n+1>. <Human-observable check>

<Start the app, open the URL, confirm the thing appears.>

## <Dangerous inverse operation>

<Unnumbered trailer, e.g. rolling back. State the hard prohibition:
 "Never <do this> in a shared or production environment.">
````

Rules that make recipes work:

- Steps are **numbered `##` headings starting with a verb** — Create, Register, Generate, Open, Review, Apply, Verify, Run.
- Verification is a **terminal step**, not a per-step field.
- Inline the code; do not point at an exemplar to copy. The recipe *is* the exemplar.
- Duplicate overlapping steps across recipes rather than cross-linking them.
- No tables, no checkboxes, no emoji inside recipes.

Which chores earn a recipe: done more than twice, **and** multi-file with a
fixed order, **and** containing at least one wiring step that silently no-ops
when skipped. Migrations and "add a new <unit>" almost always qualify.
