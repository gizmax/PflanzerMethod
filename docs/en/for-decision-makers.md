**Pflanzer Method | pflanzer.cz/method**

> English version of [pro-decidera.md](../pro-decidera.md). The Czech original is authoritative.

# For the sponsor: what we ask of you

> Who this is for: the **Decider**, the person who will make the decision. One page, a 3-minute read.

## The problem

The path from an idea to something that works takes months. The brief travels
from business to product, to development, to security and to operations, and
every handover loses context. You decide on slides and specifications, not on
something you can try for yourself.

## What you get

In about a week:

- **three running variants** of the solution on our real repo. You open them
  in the browser; they are not mockups;
- **a decision made on the code**: Go, Kill, or one round of changes (Iterate);
- **the winner as a pull request** that has passed the automatic checks and the
  security and operations sign-offs, with nothing rewritten afterwards;
- **a decision record in git**: who decided what, why, and who signed off.

## What we need from you

1. **A mandate to say both Go and Kill.** If you cannot stop it, you are not the Decider.
2. **15 minutes at the start** (Kickoff): you agree the problem in one sentence,
   the one number that means success, and when we wrap up. You also answer
   the question "How serious is this?" (demo / pilot / production, and whether
   the data contains personal data). This signs off the brief on your behalf and
   determines how many windows are needed.
3. **90 minutes at the end** (Decision): you see the variants running, hear the
   three biggest disputes and decide. You vote **last**, so the team does
   not say what you want to hear.
4. **Names**: whom you appoint for product, design, development, security & legal
   and operations.

Nothing more. You do not need to be at the Build. No extra money is needed
beyond the Claude Code licence the developers already have. AI usage is measured
and you will see it in the final record.

## Risk and how it is controlled

| Concern | What guards against it |
|-------|-------------|
| "AI will write unsafe code" | a 20-minute security & legal **checkpoint** on the running variants (for a pilot without personal data, one merged Security and operations window); nothing is deployed without a sign-off |
| "Nobody is accountable" | decisions and sign-offs with **names** in `.pflanzer/decisions/` (git) |
| "The code won't be good enough" | **automatic checks** (lint, tests, build, security) on the winner only; below a score of 80 (pilot) / 85 (production) out of 100 it goes no further without your explicit exception |
| "We'll spend more than expected" | the AI cost cap is confirmed at the checkpoint and the usage is in the record |
| "It will never end" | Iterate only once; after that, Go or Kill |
| "We lack a specialist" | AI prepares a pre-check, but for a pilot and production **a person always signs off**; AI never replaces you (the Decider) or development |
| "Security won't sign off" | you decide: for a pilot without personal data you can knowingly accept the risk (`--override-triage`, your name is recorded); legal is not covered by this |
| "I want to be at the Build" | no, so that your opinion does not steer the vote; you get a 10-minute screencast of the Build and at the Decision you see the variants live |

## A ready-made email

**Subject:** Pflanzer Method pilot: I need you for 15 min + 90 min

> Hello,
>
> we want to try an approach where, in about a week, we have three running
> variants of a solution to [problem in one sentence] on our real repo, and
> you decide on them. The winner goes out as a pull request through our usual checks.
>
> I need from you:
> 1. A mandate to say both Go and Kill.
> 2. 15 minutes for Kickoff: [date, time] (the problem, the success number, when we finish).
> 3. 90 minutes for the Decision: [date, time] (you see the variants running and decide).
>
> You do not need to be at the Build. One-page overview:
> https://pflanzer.cz/method
>
> Thank you,
> [name]

Your next step: send the email and block both dates. The product manager handles
the rest following [`getting-started.md`](getting-started.md).
