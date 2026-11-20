# Notes - Team Char Siu

## How the model works
- 500 agents by default (--n changes it) in one 100x100 box. 4 groups (A to D), each with a meeting point.
  About 20% of agents have no group.
- States: unaware, spreader, corrector, stifler.
- One step (stepSimulation): move, tick the timers, spread, maybe add correctors.
- Movement (movement.py):
  - group member: random walk, kept within `leash` of the meeting point
  - no group: random walk anywhere in the box
  - each step a group member has a `travelChance` of visiting another group. They walk there at
    `travelSpeed`, stay `stayLength` steps, then walk home
- The rumour is about one agent, the subject, who is in group D. Patient zero is one agent in group A.
- Spread uses a distance matrix like the article. Two agents are in contact if they are closer than
  `contactRadius`. Contact is between any agents, so groups mix where the circles overlap, through
  visitors, and through no-group agents.
  - P(rumour) = 1 - (1 - g * rumourStrength)^(spreaders in contact)
  - P(correct) = 1 - (1 - (1 - g) * correctionStrength)^(correctors in contact)
  - g = gullibility. If both happen in one step it's a coin flip. Spreaders can switch to corrector.
- Hearing the rumour isn't the same as passing it on. Each agent has an interest (0 to 1). If they hear
  it they pass it on with chance minInterest + (1 - minInterest) * interest, otherwise they go straight
  to stifler. They stay in the sim, they just don't spread it.
- When the subject hears it they deny it and become the first corrector, so the correction only starts
  once the rumour has reached them.
- Spreaders and correctors become stiflers after 50 steps.
- Everyone decides from the old states and the changes are applied at the end, so the order of agents
  doesn't matter.

## Article vs ours
| Article | Ours |
|---|---|
| everyone random in one box | groups with meeting points, no-group agents, visits between groups |
| saved GIF | live window, `--headless` for benchmarks |
| infected / healthy | 4 states |
| roll > resistance | roll < gullibility |
| updates in place | read old state, write new state |
| one disease | rumour about a subject + a correction |

## Seeds
One seed decides the whole run (np.random.seed in makeAgents). Default is 42. Same seed + n + settings
gives the same run. For serial and parallel to match exactly we'll need random numbers from
(seed, step, agent) instead, see todo 1.

## Settings
`rumourStrength`, `correctionStrength`, `travelChance`, `leash` and `minInterest` were found by trial and
error, not from data. `contactRadius` is scaled with n so agents meet about the same number of people at
any n. In our test runs (500 agents, 250 steps) the rumour reached roughly 250 to 360 agents and the
subject heard it around step 90 to 120.

## Todo
1. Random numbers from (seed, step, agent) instead of np.random so serial and parallel match.
2. Agent objects to numpy arrays (Numba can't use objects).
3. Replace the O(n^2) distance matrix with a grid / cell list. The matrix is about 200 MB at 5,000
   agents and about 3 GB at 20,000, so we need this for big n.
4. Numba `prange` version.
5. Equivalence test: same seed, serial output == parallel output.
6. Benchmarks (headless only): n in {1k, 10k, 100k}, workers in {1, 2, 4, 8}. Time, speed-up S = Ts/Tp,
   efficiency E = S/p.
7. Experiments: vary travelChance, noGroupFraction, minInterest, subjectDenies.
8. Report, viva prep.

## Parallel plan
- Movement and spread: each agent reads old state and only writes its own slot, so it's safe to split
  by agent.
- The distance matrix is the bottleneck. A cell list takes it from O(n^2) to roughly O(n).
- Groups make agents cluster, so the work per cell is uneven. Measure the load imbalance.
- Never benchmark with the live window. Use `--headless`.
- Expect poor speed-up for small n. Report it.

## Maybe later
Rumour text mutation using a transmission log and a separate post-processing module, outside the
simulation loop.

## Questions for Joseph
1. Is a rumour acceptable instead of a disease?
2. Any limits on language or libraries? (Python + Numba planned)
3. Is a live window enough for the graphic output, or do we also need a saved image/video?
4. Target population size?
5. Is shared-memory parallelism enough?
