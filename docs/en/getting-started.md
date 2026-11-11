**Pflanzer Method | pflanzer.cz/method**

> English version of [zacni.md](../zacni.md). The Czech original is authoritative.

# Getting started: your first Pflanzer Method pilot

> Who this is for: the **builder** (product manager or developer) who sets the pilot up.
> Send your boss (the Decider) [`for-decision-makers.md`](for-decision-makers.md). The process in one picture
> is in [`postup.md`](../postup.md) (CS). Exceptions and "what if..." are in [`faq.md`](../faq.md) (CS).

The method: a small group with representatives from the whole path, from idea
to operations, builds three running variants with AI on your real repo. The
Decider decides on them, and the winner goes out as a PR. You need
**about 1 week of preparation** (mostly calendars) and **about 8 days** for the
pilot. It suits a smaller piece of work with one metric. It does **not** suit
payments, regulated banks, native mobile apps, or a project without a person
who may say both Go and Kill. See the [30-second test](../faq.md#hodí-se-to-pro-nás) (CS).

## What it costs

The plan from Kickoff depends on the level and the risk profile: a Lean pilot
takes **about 6–8 person-days**, a Quick demo about 5, a production rollout
about 14 (`report summary` shows the figure with its source). There is no
licence beyond Claude Code. The Decider gives **15 min + 90 min**, security & legal
and operations give **20 min** each.
The table and a text for your boss: [`faq.md`](../faq.md#kolik-to-stojí) (CS).

## Checklist before the start

- [ ] The problem in 1 sentence + 1 metric + a kill criterion
- [ ] **A name for each of the 6 steps of the path**: business (the Decider, who may
      say both Go and Kill), product, design, development, security & legal,
      operations. One person may cover several steps. Where nobody is available, see
      [What if we don't have...](../faq.md#co-když-nemáme) (CS)
- [ ] All windows are in the calendar (table below)
- [ ] A preview environment for the variants, agreed with operations (or
      [`pflanzer share`](../faq.md#tunel-lan-a-preview) (CS))
- [ ] `pflanzer doctor` reports "ready for Kickoff: yes"

At most 5 people at a time. A step with no name and no permitted AI stand-in means: do not start the pilot.

## Installation (developer, ~30 min)

Prerequisites: `git`, `python3 ≥ 3.10`, `node ≥ 20.11`,
[Claude Code](https://claude.com/claude-code). What the script changes:
[`faq.md`](../faq.md#instalace-v-korporátu-co-přesně-skript-dělá) (CS).

```bash
curl -fsSL https://raw.githubusercontent.com/gizmax/PflanzerMethod/main/install.sh | bash   # jednou na stroj
cd /cesta/k/vasemu/repu && pflanzer init     # jednou na repo
# INTEGRATION_GUIDE: 5 min přes Claude Code („vyplň docs/INTEGRATION_GUIDE.md podle tohoto repa“),
# ručně ~30 min; výsledek zkontroluj. Zkontroluj i .pflanzer/CONSTITUTION.md.
git add -A docs .pflanzer tests .gitignore .claude/settings.json && git commit -m "chore(pflanzer): init" && git push -u origin HEAD
pflanzer doctor                              # je repo připravené?
```

(The comments in the block are in Czech, as in the original. In English: once per machine; once per repo; INTEGRATION_GUIDE takes 5 min through Claude Code, about 30 min by hand, so check the result, and check `.pflanzer/CONSTITUTION.md` too; is the repo ready?)

After that, in Claude Code in that repo, **`/pm`** is enough. It finds out the
state and tells you the one next step. In a fresh repo `/pm` also runs `init` and
`doctor` for you.

For several repositories (web + API): `pflanzer init` belongs in each of them.
Details in [`faq.md`](../faq.md#projekt-přes-víc-repozitářů) (CS).

## The path, step by step

Each step needs one command (in Claude Code, `/pm <step>`).

| # | Step | Command | Who, how long |
|---|------|---------|---------------|
| 1 | Kickoff: a one-page brief, names for the 6 steps, the question "How serious is this? demo / pilot / production" | `/pm start` (without Claude Code: `pflanzer start --spec kickoff.json`) | Decider + core group, 15 min |
| 2 | Build: AI builds 3 variants, checks run continuously | `/pm build` (help: `pflanzer build`; writing code by hand? `pflanzer worktree setup --slug S --builder manual`) | core group, 3 h |
| 3 | Record the Build assessment (the web hub shows no variants without it) | `pflanzer record --spec soubor.json` | builder |
| 4 | Share: preview and web hub, one address + password, a ready message to colleagues | `pflanzer share --slug S` | builder, 5 min |
| 5 | Collect feedback (Async): representatives click through and comment | `/pm feedback` (terminal: `pflanzer feedback add --slug S --variant A --role Design --by "Jméno" --severity critical\|major\|minor --text "…"`, overview `pflanzer feedback list --slug S`) | everyone, ~15 min a day, 3–5 days |
| 6 | Decision: demo, top 3 disputes, the Decider votes last → Go / Iterate (max 1×) / Kill | `/pm decide` (`pflanzer decide`) | Decider + core group, 60–90 min |
| 7 | Ship: checks on the winner only, the tool produces `SHIP.md` and the PR text; the repo owner opens the PR with the `gh pr create` command from the end of `SHIP.md` | `/pm ship` (`pflanzer ship --slug S`) | developers + operations, 1–2 days |
| 8 | Retro: how much of the winner's code lives in production | `/pm retro S` (`pflanzer retro measure --slug S --pr-url URL`, without gh `--merge-commit <sha>`) | builder, after merge |

Kickoff prints the (short) slug. You can also set it in the spec (`"slug"`).
After feedback collection (after the Decision) you stop sharing:
`pflanzer share down --slug S`. Report for leadership:
`pflanzer report summary --slug S`. The deadline in the message to colleagues is
calculated from the length of feedback collection. To set your own, run
`pflanzer share --slug S --deadline "pátek 17:00"`.
Feedback summary: `/pm feedback` (terminal `pflanzer feedback_pull --slug S`).
**Where are you?** `/pm` tells you the phase and the one next step. Decisions are
written to the repo (`.pflanzer/decisions/<slug>.md`), so commit them. In a hurry?
`/pm live "co řešíme"` combines Kickoff and Build (level Quick, 60–90 min).

### How serious is this?

Kickoff asks only this: is it a **demo** (throwaway), a **pilot**, or
**production**, plus whether the data contains personal data
(`personal_data: true` means data class L3 at least. A lower `data_class` is
overwritten to L3 with a warning, so a pilot with personal data never gets the
merged window). The level (Quick / Lean / Full), the windows, the build mode and
the thresholds are derived from this. You can override them
([`faq.md`](../faq.md#výjimky-a-přebití-prahu) (CS)). Ship threshold: pilot ≥ 80,
production ≥ 85 out of 100 (throwaway: the score is informative and does not block Ship).

| Answer | Level | Windows to sign off |
|---|---|---|
| demo | Quick | none (triage does not run; a new Kickoff is needed before a pilot) |
| pilot without personal data | Lean | **Brief** (signed automatically at Kickoff) + **Security and operations** (`checkpoint … bezpecnost-provoz`) |
| pilot with personal data | Lean | Brief, Security & legal, Operations |
| production | Lean (Full with personal data) | Brief, Security & legal, Operations (with Full, Legal (DPIA) separately only when triage defers the DPIA) |

### Windows and sign-offs

| When | What | Who |
|--------|-----|-----|
| Day 0 | Kickoff, 15 min | Decider + core group |
| Day 1–5 | Build, 3 h + security & legal checkpoint, 20 min | core group (+ security & legal) |
| Day 1–6 | Feedback collection, 3–5 days | everyone |
| Day ~7 | Decision, 60–90 min | Decider + core group |
| Day ~8 | Ship, 1–2 days + operations checkpoint, 20 min | developers + operations |

A window is signed off with one command: `pflanzer checkpoint --slug S
bezpecnost|provoz|bezpecnost-provoz --by "<name>" --note "…"`. **The Brief is signed
off automatically at Kickoff** in the Decider's name (when the spec contains the
metric, the kill criterion and the names for the steps). `pflanzer status` shows it
among the sign-offs. Sign it by hand
(`checkpoint … zadani --by "<name of the Decider>"`, a name, not the word "Decider")
only when Kickoff ran without a metric or kill criterion. Without sign-offs, Ship of a
pilot does not pass. Where AI stood in for a window, it is recorded as a proposal
(`--ai --agent <agent>`) and a person signs it off. **Design by AI** is already
recorded at Kickoff: a person (the product manager) only confirms with
`pflanzer checkpoint --slug S design --by "Jméno" --note "co jste zkontrolovali"`.
Use `--ai` only when the AI proposal arises after the fact. Who signs off when
there is no security person: [`faq.md`](../faq.md#security-nebo-dpo-na-plný-úvazek) (CS).

### Without Claude Code

Kickoff also works from the terminal. Write the spec to `kickoff.json` and run
`pflanzer start --spec kickoff.json` (all fields: `pflanzer start --help`).

```json
{"hook": "Rychlejší schvalování žádostí", "decider_name": "Dana Nováková",
 "risk_profile": "pilot", "personal_data": false,
 "metric": "10 z 15 lidí otevře přehled 3× týdně do 30 dnů",
 "kill_criteria": "do 30 dnů přehled otevře méně než 5 lidí",
 "target_repo_url": "https://github.com/firma/appka",
 "path_owners": {"byznys": "Dana", "produkt": "Petr", "design": "AI", "vyvoj": "Tomáš",
                 "bezpecnost": "Jana", "provoz": "Karel"}}
```

The example values are in Czech, as in the original. In English: hook "Faster approval of requests";
metric "10 of 15 people open the overview 3 times a week within 30 days"; kill criterion "if fewer than 5 people open the overview within 30 days".

Level Full (production with personal data) is recommended by `/pm triage`. Without
Claude Code, write the 4 results (discovery, security, legal, platform) to
`triage.json` and run `pflanzer triage --spec triage.json` (schema and example:
`pflanzer triage --help`, [`faq.md`](../faq.md#triage-bez-claude-code) (CS)).
`signed_by` in triage is a person's sign-off. Empty means it is waiting for a sign-off.

More terminal steps: `pflanzer build` (help for Build), `pflanzer prompts --slug S`,
`pflanzer record --spec soubor.json` (records the Build), `pflanzer share --slug S`
(sharing for feedback collection), `pflanzer decide`, `pflanzer ship`.

## Stuck?

`/pm` is not in Claude Code → restart Claude Code, try `/pflanzer:pm`.
`pflanzer: command not found` → `export PATH="$HOME/.local/bin:$PATH"`.
Everything else: [`faq.md`](../faq.md#když-se-něco-zasekne) (CS). What to measure and a glossary:
[`faq.md`](../faq.md#co-měřit) (CS), [`methodology/glossary.md`](../methodology/glossary.md) (CS).
