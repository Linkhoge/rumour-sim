# Notes - Team Char Siu

## Model
- 500 agents in one 100x100 box. 4 groups (A-D), each with a meeting point. About 20% of agents have no group.
- States: Unaware, Spreader, Corrector, Stifler.
- Each step (`stepSimulation`): move, tick counters, spread, maybe seed correctors.
- Movement (`movement.py`):
  - Grouped agent: random walk, kept within `leash` of its group's meeting point.
  - No-group agent: random walk anywhere in the box.
  - Each step a grouped agent starts a visit to another group with `travelChance`. It walks there at `travelSpeed`,
    stays `stayLength` steps, then walks home.
- Spread: distance matrix (article). Contact if distance < `contactRadius`. Contact is between any agents, so
  groups mix where circles overlap, through visitors, and through no-group agents.
  - P(rumour) = 1 - (1 - g * rumourStrength)^nSpreaderContacts
  - P(correct) = 1 - (1 - (1 - g) * correctionStrength)^nCorrectorContacts
  - g = gullibility. Both in one step: coin flip. Spreaders can switch to corrector.
- Spreaders/correctors become stiflers after 50 steps.
- Rumour starts in group A (5 spreaders). Correction starts at step 60 with 5 agents.
- Updates use old states, applied at the end (order independent).

## Article vs ours
| Article | Ours |
|---|---|
| Everyone random in one box | Groups with meeting points, no-group agents, visits between groups |
| Saved GIF | Live matplotlib window (`FuncAnimation`), `--headless` for benchmarks |
| Infected / healthy | 4 states |
| roll > resistance | roll < gullibility |
| In-place update | Old state read, new state written |

## Settings
`rumourStrength`, `correctionStrength`, `travelChance`, `leash` found by trial and error, not from data.
Seed 42 defaults: rumour reaches B, C, D around step 40-60.

## Todo
1. Replace `np.random` with RNG from (seed, step, agent) so serial and parallel match.
2. Convert Agent objects to NumPy arrays (Numba cannot use objects).
3. Replace the O(n^2) distance matrix with a grid / cell list. Needed for large n.
4. Numba `prange` version.
5. Equivalence test: same seed, serial output == parallel output.
6. Benchmarks (headless only): n in {1k, 10k, 100k}, workers in {1, 2, 4, 8}. Time, speed-up S = Ts/Tp, efficiency E = S/p.
7. Experiments: vary travelChance, noGroupFraction, correctionStart, correctionStrength.
8. Report, viva prep.

## Parallel plan
- Movement and spread: each agent reads old state and writes only its own slot. Safe to split by agent.
- Distance matrix is the bottleneck. Cell list takes it from O(n^2) to roughly O(n).
- Groups make agents cluster, so work per cell is uneven. Measure load imbalance.
- Never benchmark with the live window. Use `--headless`.
- Expect poor speed-up for small n. Report it.

## Optional later
Rumour text mutation via a transmission log and a separate post-processing module, outside the simulation loop.

## Questions for Joseph
1. Rumour spread acceptable instead of disease?
2. Any limits on language/libraries? (Python + Numba planned)
3. Is a live window enough for "graphic output", or do we also need a saved image/video?
4. Target population size?
5. Shared-memory parallelism enough?
