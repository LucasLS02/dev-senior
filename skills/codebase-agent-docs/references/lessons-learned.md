# Lessons Learned

Patterns and anti-patterns observed in a production agent-doc set (~1400 lines
across 18 files, covering a Python/FastAPI integration platform). The forms
generalize; the contents never do.

---

## The router pattern

The root file works as a router because each section points at exactly one
place and the one-line gloss tells the agent whether to follow the link **for
this task**. An agent that opens the router spends ~110 lines and then knows
which 60 lines it actually needs.

**Anti-pattern:** detailed rules in the router. The agent pays for details it
does not need, on every task. Measured shape of a healthy router: 4 tables,
3 code blocks, 1 bullet list, and no procedure at all.

**Anti-pattern:** a router that grows. When a section outgrows the ceiling, it
becomes a topic file and the router gains one index row. The router's line
count should be roughly constant over the life of the project.

---

## Gotchas are the highest-value file

It repeatedly saves more time than anything else, because it captures what
cannot be grepped: invariants spanning files, and failures that produce no
error.

The three-beat anatomy is what makes an entry useful — mechanism, **silent**
consequence, imperative correction. The middle beat is the filter. Recurring
vocabulary in the real file: "silently", "no warning", "silent bug with no
exception", "breaks the client contract silently (wrong JSON shape, no error)".

**When to add one:** a reasonable senior developer would get this wrong, *and*
getting it wrong does not raise. If it throws a clear exception, the exception
is already the documentation.

**Best source of candidates:** `git log --grep='^fix'`. Every fix commit is a
trap somebody already fell into. Read the diff, not just the subject.

**Granularity is a hard rule:** one trap, one `##` section, ~6 lines. In the
reference set, gotchas is the second-longest file but has the smallest
sections. Merging two traps into one section hides one of them.

---

## Protected-file lists are cheap and prevent expensive mistakes

Four categories, sorted by *why* rather than by file type, and the verdict
lives in the heading (`— never hand-edit`, `— never commit`, `— change with
care`):

1. Generated files — with the regeneration command, so the rule has an escape hatch
2. Secrets — absolute, plus "never log their contents"
3. Load-bearing config — with the specific risk named, so the rule is arguable
4. **Manually-maintained critical files** — the inverse rule: you must remember to update these

Category 4 is the one most projects omit, and the one that causes silent
breakage. A file can appear in both 3 and 4.

---

## Work rules: 13 is about right

Numbered imperatives, one situation each. Fewer than 6 and agents miss common
edge cases; more than 20 and they stop reading carefully. The load-bearing ones
are always "read the source before claiming anything about it", "do not commit
without approval", "do not push or rewrite history without approval". Project
rules go at the end.

---

## Model strategy up front

Most agents have no default policy for which model to use for what. A short
list at the top of `workflow.md` ("planning → the reasoning model; mechanical
implementation → the fast model") measurably improves output, and it costs four
lines.

---

## Recipes pay for themselves immediately

Write one for any chore done more than twice that is multi-file with a fixed
order. The value is concentrated in two things: **step ordering** (register the
model in the metadata file *before* autogenerating, or the migration comes out
empty) and **wiring steps that silently no-op when skipped**.

Recipes inline skeletal code rather than pointing at an exemplar — the recipe
*is* the exemplar. They duplicate overlapping steps instead of cross-linking,
because an agent mid-task should never have to open a second file.

Verification is a terminal step, not a per-step field. The last steps are
always the project's real validate and test commands, plus one
human-observable check where one exists.

---

## Anatomy and recipe are different genres

Anatomy = the target state (tree → one skeleton per file → `Rules:` bullets).
Recipe = the ordered procedure. Merging them produces a document that is bad at
both: too long to follow as steps, too procedural to consult as a reference.

The anatomy file is the highest-leverage one to port to a new project, because
every codebase has a repeated unit — a feature folder, a package, a resource, a
module. Name the file after that unit.

---

## Directory guides: short, and disjoint from the root

Three jobs: an inventory of what lives here, the local naming convention, the
local traps. Nothing else.

**Anti-pattern:** duplicating `docs/agents/` content into a directory guide.
Pick one home per fact. The reference set has exactly one deliberate
duplication — the service registration order, repeated in the root and in the
infra guide, because it is the single fact that defines that directory.

Directory guides also do not link to each other, and mostly do not link back to
the root. The agent is assumed to arrive from the root or from the filesystem.

---

## The link graph must terminate

Topic files carry ~1 link each — 3 in 692 lines in the reference set. The
router links; the leaves do not chatter. When two leaves need the same fact,
duplicate it; a cited `file.py:NNN` appearing in two topic files is correct,
not a defect.

This is what makes the set cheap to read: an agent following links never
discovers it has opened six files.

---

## The truth sources table

Three to seven rows mapping a question to the file that *defines* the answer.
Beyond seven the signal dilutes and agents go back to guessing.

The subtle part: a diagram and its truth source belong in different files on
purpose. The state machine ASCII lives in the directory guide; the truth
sources table points at the enum that defines it. The diagram is a convenience
and is allowed to go stale; the code is not.

---

## Conflict resolution: "trust the code" is the right default

Earlier versions of this skill recommended the opposite ("docs prevail, the
code is wrong"). That is correct only in a spec-driven repo where docs are
reviewed as strictly as code. Everywhere else it makes agents "fix" working
code to match stale prose — an expensive and hard-to-spot failure.

The production wording, three rules in three sentences:

> When this file and the code disagree, **trust the code**. This file describes
> intent; the code is ground truth. File a doc fix alongside any code change.

Precedence, the reason for the precedence, and the maintenance obligation. The
third sentence is what stops the docs decaying under the first.

---

## Language: decide once, state it explicitly

Detect the project's dominant prose language from the README and recent commit
subjects, then keep it consistent across the whole set. Code identifiers,
commands and paths always stay as they are in the repo.

Mixed-language doc sets drift: in the reference project the agent docs are
English while the user-facing docs and plans are Portuguese, and that split
only works because it is stated and stable. An undeclared split produces
half-translated files within a year.

---

## State machines deserve their own section

If the domain has them, give each an ASCII diagram, list the transitions as
explicit bullets, and mark which ones only an external system may perform.
Put the most dangerous constraint in `gotchas.md` too — redundancy is correct
here, because the agent that is about to break the invariant is reading
gotchas, not the diagram.

---

## Aspirational vs actual structure

When the canonical structure is not implemented everywhere, say so in the
anatomy file:

> Status: <n> of <m> modules have the full canonical structure. The structure
> documented here is **aspirational** — it defines the target, not the current
> state.

Without this, an agent reads a real module, sees it diverge, and concludes the
docs are wrong about everything.

---

## Bold discipline

Bold marks **the token that causes the bug if misread** — a port number, a
"before", a "not". Never a whole rule, never ordinary emphasis. In a file where
every rule is bolded, none of them is.

Same logic for shouting caps: the reference set uses plain-cased "Never" and
"Do not" at the start of sentences and reserves `NEVER` for the top-level
CLAUDE.md. Two levels of emphasis is one more than most docs earn.
