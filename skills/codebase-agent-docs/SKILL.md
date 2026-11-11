---
name: codebase-agent-docs
description: >-
  Builds AI-agent-optimized documentation for any codebase — a root AGENTS.md
  router, directory-level AGENTS.md guides, and docs/agents/ topic files and
  recipes that let an agent navigate and safely modify a project it has never
  seen. Analyzes the project first with parallel sub-agents, then generates.
  Use when setting up agent documentation for a project, auditing existing
  agent docs for gaps, or porting this structure to another repo. Triggers:
  "create agent docs", "set up AGENTS.md", "document codebase for agents",
  "agent documentation", "/agent-docs".
---

# Codebase Agent Docs

Builds a **hub-and-spoke documentation system**: one router file an agent reads
first, and a flat set of leaves it reads only when the current task needs them.

The point is not completeness. It is that an agent can read the *whole set*
without burning its context, and that every line it reads is a fact it could
not have grepped.

## The model

```text
AGENTS.md                    ← router. Zero procedure. Links only.
 ├─ ## Topic index    → docs/agents/*.md        (subject matter)
 └─ ## Layer guides   → <dir>/AGENTS.md         (locations)

docs/agents/*.md     ← leaves. Near-zero links between them.
                       The graph terminates here. No cycles.
```

Router linking is one-way and depth-1. Leaves do not chatter at each other;
when two leaves need the same fact, **duplicate it** rather than cross-link.

## Hard constraints

Measured from a production reference implementation. These are what keep agent
docs read instead of skimmed — treat them as limits, not suggestions.

| Constraint | Value |
|---|---|
| Root `AGENTS.md` | ~110 lines, hard ceiling 120. Contains **no** how-to procedure |
| Directory `AGENTS.md` | 25–75 lines, 3–6 `##` sections |
| Topic file | 40–140 lines |
| Section | ~11 lines average, ~20 maximum |
| Heading depth | **2 levels. Never use `###`** |
| Gotcha granularity | one trap = one `##` section. No exceptions |
| Links inside a topic file | ≤1. The router does the linking |
| Total surface | under ~700 lines for a full platform |

If a navigation file passes its ceiling, the overflow becomes a new topic file
registered in the router index. Growing the router is always the wrong fix.

## Admission test

Before writing any line, ask: **would `grep` answer this?** If yes, leave it
out.

Include facts that are invisible or costly to derive from the tree:

- **Ordering facts** — registration order, "create the migration before the service"
- **Silent failures** — "omitting it silently skips auditing; there is no warning"
- **Negative space** — what to *delete* (`cp .env.example .env # then remove X`), what does not exist, what the product does NOT do
- **Non-default config** — a task queue on threads, not prefork; a DB on port 8432, not 5432
- **Test-interaction quirks** — fixtures that skip tables, dialect differences
- **Defaults the code hides** — and behaviour that looks like a bug but is not

Exclude: function signatures, parameter lists, example payloads, explanations
of the framework itself, rationale essays, history, roadmap, TODOs.

## Phase 1 — Analyze, sub-agent driven

Never read the whole repo in the main context. Dispatch these lanes **in
parallel**, one agent each, and keep only their reports.

| Lane | The agent reads | It returns |
|---|---|---|
| 1. Product & stack | README, manifest (`pyproject.toml`/`package.json`/`go.mod`/`Gemfile`), lockfile versions | what the product does, what it explicitly does NOT do, pinned versions, every non-default choice |
| 2. Architecture | dir tree to depth 3, app/server entry point, route or module registration | layer map, entry points, wiring that happens automatically |
| 3. Exemplar unit | the single most-repeated unit — one domain module, feature folder, package, or resource | its exact internal file layout and the role of each file |
| 4. **Traps** | `git log --oneline --grep='^fix'`, test conftest/setup, CI config, `.env.example` | candidate gotchas. **Highest-value lane** — a fix commit is a trap someone already hit |
| 5. Protected surface | `.gitignore`, generated/codegen output, migration dir, secret files, lockfiles | what must never be hand-edited, never committed, changed only with care |
| 6. Conventions | linter config, last ~50 commit subjects, PR template, test naming | lint rules, real commit examples, branch naming, test taxonomy |

Then detect the **documentation language**: read the README and the last 50
commit subjects. Write the agent docs in the project's dominant prose language;
keep code identifiers, commands and paths exactly as they appear in the repo.
State the choice explicitly in the style topic file so it stops being
re-litigated.

Do not write a file until the fact sheet is filled: product purpose and
anti-purpose, stack with versions, run/test/validate commands, layer map,
automatic wiring, protected files, and at least five real traps.

## Phase 2 — Generate, leaves before root

Dependency order. The router's index can only be honest once the leaves exist.

1. **Topic files** (`docs/agents/*.md`) — they hold all the content
2. **Recipes** (`docs/agents/recipes/*.md`)
3. **Directory `AGENTS.md`** — inventory of what lives there, local convention, local traps
4. **Root `AGENTS.md` last** — product, stack, commands, architecture, topic index, layer guides, truth sources, conflict resolution

### Which files to create

| Always | Add when the project has it |
|---|---|
| `workflow.md` | `<unit>-anatomy.md` — name it after whatever the repo repeats most (module, feature folder, package, resource) |
| `gotchas.md` | `development.md` — shrinks to a few lines if setup is standard |
| `dont-touch.md` | one topic file **per subsystem that has bitten someone twice** (auth, deployment, background jobs, state management…) |
| `tests.md` | a recipe for any chore done more than twice |
| `code-style.md` | a directory `AGENTS.md` per real structural layer |
| `commits-prs.md` | |

An empty section is worse than a missing file. Delete any slot you cannot fill
with non-obvious content.

See `references/templates.md` for the skeleton of every file type.

## Phase 3 — Validate

Run these. Every failure is a real defect.

```bash
wc -l AGENTS.md $(find . -name AGENTS.md -not -path ./AGENTS.md) docs/agents/*.md
grep -rn '^### ' AGENTS.md docs/agents/            # must be empty
grep -c '](' docs/agents/*.md                      # each ≤ 1
grep -o '](\([^)]*\))' AGENTS.md | tr -d '](' | while read -r f; do
  [ -e "$f" ] || echo "BROKEN LINK: $f"
done
```

Then check by reading:

- [ ] Root has no how-to steps — only description, tables, and links
- [ ] Every topic file is reachable from the root index, and nothing is listed that does not exist
- [ ] Every gotcha states a consequence, not just a rule
- [ ] Every prohibition carries its reason
- [ ] Each recipe is numbered actions ending in the project's real validate + test commands
- [ ] Conflict resolution is stated once, at the root
- [ ] No section duplicates another file except one deliberate, named repetition

## Writing rules

- **Anatomy of a gotcha — three beats, fixed order.** An assertive `##` heading; the mechanism with the exact symbol; the consequence, stressing its *silence*; the imperative correction. The consequence beat is the filter: **if the failure is loud, it is not a gotcha.**
- **Contrastive phrasing.** `X, not Y` — "UUID v7, not UUID v4", "increment by returned IDs, not input IDs". Naming the wrong thing lets an agent recognize its own mistake.
- **Bold marks the surprising token, never the rule.** Bold the word that causes the bug if misread: port `**8432**`, `**before**` the write, `**Does NOT**`. Bolding whole rules destroys the signal.
- **Every prohibition gets its reason.** "Do not use `--no-verify` to bypass them. Fix the lint issue instead."
- **Imperative, no hedging.** No "you", no "we", no "should", no "consider".
- **Tables for enumerable facts, prose for causal ones.** A table row is one clause; if it needs a paragraph, it is not a table row. A table may be followed by the one sentence it cannot express.
- **Real examples only.** Harvest commit messages from actual history; point at a real exemplar test file. Invented examples teach invented conventions.
- **Anatomy describes the target state; a recipe describes the procedure.** Never merge them.
- Paths and symbols in backticks, repo-relative, `<name>` for placeholders. Use `file.py:NNN` only when the fact lives on one hard-to-find line.
- Numbered lists written as `1.` for every item; let the renderer count.
- Match the repo's own markdown line width if it lints markdown.

## Conflict resolution — get this right

State it once, at the root, and pick the honest direction:

> When this file and the code disagree, **trust the code**. This file describes
> intent; the code is ground truth. File a doc fix alongside any code change.

The inverse ("docs prevail, the code is wrong") is only correct in a spec-driven
repo where docs are reviewed as strictly as code. Choosing it by default makes
agents "fix" working code to match stale prose.

Pair it with a **truth sources** table — 3–7 rows mapping a question to the file
that authoritatively answers it. More than seven dilutes the signal.

See `references/lessons-learned.md` for patterns and anti-patterns observed in
production agent docs.
