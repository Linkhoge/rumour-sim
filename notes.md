# Technical notes

Current specification. Supersedes the standalone friendship/viewer update notes.
Historical experiment counts are not current defaults or benchmark results.

## Model

| State | Meaning |
|---|---|
| Unaware | Has not accepted rumour or correction |
| Spreader | Actively shares rumour |
| Corrector | Actively shares correction |
| Stifler | Inactive: silent believer, expired sharer or explicit rejecter |

Belief, sharing, friendship and avoidance are separate. Timer expiry preserves
belief. Correction clears belief/avoidance, not lost friendships. Previously
corrected stiflers cannot be reactivated by correction exposure.

- Domain: 100x100. Centres: (33,33), (67,33), (33,67), (67,67). Group radius: 15.
- No-group probability: 0.2. Home-group visits do not change group membership.
- One patient zero in A; one unaware subject in D.
- Up to 12 friends selected across groups/no-group agents; four start near the
  subject and linger. Friends may believe and spread while remaining friends.

## Transmission

```text
P(rumour)     = 1 - (1 - gullibility * rumourStrength)^nearbySpreaders
P(correction) = 1 - (1 - openness * correctionStrength)^nearbyCorrectors
P(share | accepted) = minInterest + (1 - minInterest) * sharingTendency
```

Sharing tendency reuses interest. Openness and loyalty are independent per-agent
samples. No loudness/influence trait or downstream-reach leaderboard exists.
Contacts use distance < radius, excluding self. Transmission reads old states;
changes apply after sampling. If both messages succeed for an unaware agent,
a fair coin selects one. Source attribution samples a nearby active sender
uniformly; it does not log every conversation.

Rumour acceptance without sharing creates a silent believer. Failed acceptance
leaves the agent unaware. Explicit rejection uses the subject-denial branch;
with subjectDenies=1, zero explicit rejections is expected. Uncorrected stiflers
and active spreaders may accept correction.

Direct-told counts use infector links, not descendants or correction sources.
Equal counts are valid; the current viewer still highlights the first listed
leader when counts tie. Joint-rank display remains outstanding.

## Avoidance and friendship

On first belief, a friend breaks away with probability 1 - loyalty. Breakup
forces avoidance and ends lingering. A non-friend chooses avoidance once using
avoidChance; loyal friends may remain nearby. Correction stops avoidance but
does not restore friendship.

Group members random-walk inside the target group circle or travel between
groups. No-group agents random-walk across the domain. Avoiders have a hard
exclusion radius, soft outward pressure beyond it and alternate targets when
the subject blocks a group centre. Tangential fallback remains.

safeMove checks path segments. Existing overlaps are evacuated to a feasible
boundary point; this is not speed-limited physics. A moving subject may create
an overlap between updates. Display interpolation also uses the collision guard.

The subject accumulates observations of avoiders within avoidRadius + 2.
At noticeAfter it starts correction without an invented teller/hop. Direct
rumour contact can also trigger denial.

## Step order

```text
set correction duration and pending avoidance probability
subject observation -> subject movement -> other movement / avoidance
timer expiry -> snapshot transmission -> apply transitions
configured correction seeds -> record counts
```

## Defaults

| Setting | Value | CLI |
|---|---:|---|
| Population | 500 | --n |
| Steps | 400 | --steps |
| Seed | 42 | --seed |
| Centre distance from edges | 33 | --group-spread |
| Group radius | 15 | --leash |
| Correction strength | 0.03 | --correction-strength |
| Correction active duration | 50 | --correction-duration |
| Correction radius | Contact radius | --correction-radius |
| Avoidance outer-zone multiplier | 1.15 | --avoid-visual-buffer |

Code settings: contactRadius=4*sqrt(500/n), rumourStrength=0.06,
rumour active duration=50, stepSize=1.5, travelChance=0.003, travelSpeed=2,
stayLength=40, minInterest=0.5, subjectDenies=1, avoidRadius=7,
avoidChance=0.75, noticeAfter=20, nearRadius=10, correctionStart=60,
correctionSeeds=0. No correction-count cap.

These are main.py defaults. Agent.correctionDuration and stepSimulation's
fallback still use 110 if called without matching settings.

## Rendering

Original font/sprite viewer retained. Intro: 3s hold + 2s glide; model waits.
S scales node radius with sqrt(direct recipients), with a visual ceiling only.
T retains arrows or fades them over 5s; F follows the newest gold chain.
Thin arrows: 1px transmissions, 1.5px gold/white chains. Red outer rings track
actual avoidance, not all belief. Ex-friends remain violet after correction.
Graph hover reads the nearest recorded step. Three leaderboard/log rows are
visible; top-five tracking and recent history remain.

## Implementation record

| Commit | Change |
|---|---|
| 161a6b6 | Friendship/social rules, strict avoidance, import-safe CLI, tests |
| b4e128e | Permanent correctors/wider panel; superseded |
| f2c008c | Invalid placeholder commit; repaired by e69665a |
| e69665a | Source repair, configurable correction/spacing, viewer changes |
| 732f8a3 | Original viewer, compact groups, baseline correction defaults |
| f64e8db | Red avoidance rings, thinner arrows; no model changes |

## Limits and next work

- Global NumPy RNG: draw order matters. Same seed does not establish
  cross-version reproducibility or serial/parallel equivalence.
- Dense distance/contact matrices: O(n^2) space/work.
- Printed headless runtime includes statistics/plots. Add model-only timing.
- Helper/mock tests do not validate a live Arcade context.
- Social rules and parameters are experimental assumptions, not article validation.

1. Run the complete regression suite; record environment/results.
2. Check live layout, motion, indicators and graph hover.
3. Add deterministic streams and an array-based serial reference.
4. Implement parallel version and equivalence tests.
5. Evaluate spatial indexing; measure dense-cell behaviour/load imbalance.
6. Benchmark model-only runtime, S=Ts/Tp and E=S/p across documented sizes/workers.
7. Record client feedback, experiments and attribution for submission/viva.

```powershell
python -m unittest discover -s tests -v
```
