# Notes - Team Char Siu

## How the model works
- 500 agents by default (--n changes it) in one 100x100 box. 4 groups (A to D), each with a meeting point.
  About 20% of agents have no group.
- States: unaware, spreader, corrector, stifler.
- One step (stepSimulation): the subject may notice, move, tick the timers, spread, maybe add correctors.
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
- Hearing the rumour isn't the same as believing it. Each agent has an interest (0 to 1). If they hear
  it they believe it with chance minInterest + (1 - minInterest) * interest, otherwise they go straight
  to stifler. With minInterest 0.5 that is about 75% on average. They stay in the sim, they just don't
  spread it.
- Believers keep away from the subject. A believer is a spreader, or a stifler who believed it. Each step a
  believer within `avoidRadius` of the subject is pushed away from them with chance `avoidChance`, and a
  believer from the subject's own group leaves to visit another group. Correctors, people who ignored it and
  people who haven't heard it behave as normal. A spreader who changes their mind and becomes a corrector
  stops avoiding.
- Because believers keep away, the subject may never be told directly. So the subject notices instead: each
  step we count the believers within `avoidRadius` of them, and once the total reaches `noticeAfter` the
  subject realises something is going on and denies it. The nearest believer is recorded as the one who told
  them. This is how the subject finds out in practice.
- When the subject finds out they deny it and become the first corrector, so the correction only starts
  once the rumour has got to them. `correctionStrength` is low (0.03) on purpose, so only a small pool of
  agents ends up as correctors.
- Spreaders and correctors become stiflers after 50 steps.
- Everyone decides from the old states and the changes are applied at the end, so the order of agents
  doesn't matter.

## Link to the article
The article models disease with SIR (Susceptible, Infectious, Recovered). Ours maps onto it:
- unaware = susceptible, spreader = infectious, stifler = recovered
- the article's infection rate (beta) is like our rumourStrength times gullibility per contact. Its recovery
  rate (gamma) is about 1/50 because the infected counter is 50 steps
- the article raises resistance after recovery so agents can't be infected again. Our stiflers can't be
  told again, which is the same idea
- the article's infection curve has a hump (rises, peaks, falls). Our spreader line in the counts chart
  has the same shape

## Article vs ours
| Article | Ours |
|---|---|
| everyone random in one box | groups with meeting points, no-group agents, visits between groups |
| 500 agents, 10 infected, 30% resistance, 500 steps | 500 agents, 1 patient zero, 400 steps |
| infect distance 10 in the text, 5 in the code | contactRadius 4, scaled with n |
| saved GIF | live window, `--headless` for benchmarks |
| infected / healthy | 4 states |
| roll > resistance | roll < gullibility |
| updates in place | read old state, write new state |
| one disease | rumour about a subject, believers who avoid them, and a correction |

## Seeds
One seed decides the whole run (np.random.seed in makeAgents). Default is 42. Same seed + n + settings
gives the same run (we checked two runs of the same seed give identical results). For serial and parallel
to match exactly we'll need random numbers from (seed, step, agent) instead, see todo 1.

## Settings
`rumourStrength`, `correctionStrength`, `travelChance`, `leash`, `minInterest` and the avoid settings were
found by trial and error, not from data. `contactRadius` is scaled with n so agents meet about the same
number of people at any n. In our test runs (500 agents, 300 steps, seeds 1 and 2) about 280 agents ended up
believing the rumour, 22 to 24 became correctors, and the subject found out at step 81 to 100. The number
of believers within 10 units of the subject at the end was 2 to 6, compared with 10 to 20 with avoiding
turned off. Check these again on your own machine.

## Todo
1. Random numbers from (seed, step, agent) instead of np.random so serial and parallel match.
2. Agent objects to numpy arrays (Numba can't use objects).
3. Replace the O(n^2) distance matrix with a grid / cell list. The matrix is about 200 MB at 5,000
   agents and about 3 GB at 20,000, so we need this for big n.
4. Numba `prange` version.
5. Equivalence test: same seed, serial output == parallel output.
6. Benchmarks (headless only): n in {1k, 10k, 100k}, workers in {1, 2, 4, 8}. Time, speed-up S = Ts/Tp,
   efficiency E = S/p.
7. Experiments: vary travelChance, noGroupFraction, minInterest, avoidRadius, subjectDenies.
8. Report, viva prep.

## Parallel plan
- Movement and spread: each agent reads old state and only writes its own slot, so it's safe to split
  by agent.
- Avoiding the subject only reads the subject's position and the agent's own state, so it splits by agent
  too. The subject noticing is a count over all agents (a reduction), so the parallel version needs a
  reduction step for it.
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
