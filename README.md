# Rumour Spread Simulation - Team Char Siu

Members: Ariel Fajimiyo (more to be added)

Agent-based simulation of a rumour and a correction spreading between agents that move around one
shared space. Live simulation window. Serial version, parallel version, then benchmark.

## Run
```
pip install -r requirements.txt
python main.py                                  # live window, asks for the rumour text
python main.py "rumour text"                    # live window
python main.py "rumour text" --headless         # no window, saves plots to results/ (use for benchmarks)
```
Close the live window to stop. Headless output: `results/curve.png`, `results/group_spreaders.png`.

## Reading the live window
- One shared box. Dashed circles mark where Groups A-D hang out. Circles can overlap with other agents.
- Fill colour = rumour state: grey unaware, red spreader, green corrector, dark stifler.
- Ring colour = home group. Diamonds with no ring = agents in no group (they wander anywhere).
- Group members sometimes walk to another group, stay a while, then go home.
- Right panel: live counts per state.

## Files
| File | Purpose |
|---|---|
| `agent.py` | Agent class and states |
| `movement.py` | Group meeting points, random walk, visiting other groups |
| `simulation.py` | Setup, spread rule, one step, headless loop |
| `live.py` | Live window |
| `plots.py` | Static plots for headless runs |
| `main.py` | Settings, entry point |
| `notes.md` | Technical notes |

Comments tagged `ARTICLE:` (ref 1) or `OUR OWN:`.

## Status
- [x] Agents, groups, no-group agents, movement, visiting
- [x] Rumour + correction spread, stifling
- [x] Live window + headless mode + plots
- [ ] Seeded RNG per (seed, step, agent)
- [ ] NumPy array version
- [ ] Parallel version (Numba)
- [ ] Serial vs parallel equivalence test
- [ ] Benchmarks (absolute time, speed-up, efficiency)

## References
1. Le Nguyen, "Simulation 102: Agent-Based Disease Modeling", Medium, 2023. https://medium.com/@ln8378/simulation-102-agent-based-disease-modeling-17307f2de2f3
2. Hayes, "Rumours and Errours", American Scientist. https://www.americanscientist.org/article/rumours-and-errours
3. "The Maki-Thompson rumour model: a detailed analysis". https://www.sciencedirect.com/science/article/abs/pii/S1364815200000293
4. "Theory of rumour spreading in complex social networks" (arXiv 0807.1458). https://ar5iv.labs.arxiv.org/html/0807.1458
5. "Rumour Spreading In Community Based Networks" (arXiv 2607.08546). https://arxiv.org/html/2607.08546v1
6. "Network Segregation in a Model of Misinformation and Fact-checking" (arXiv 1610.04170). https://ar5iv.labs.arxiv.org/html/1610.04170
7. "Agent Based Rumor Spreading in a scale-free network" (arXiv 1805.05999). https://ar5iv.arxiv.org/html/1805.05999
8. "Controlling the Misinformation Diffusion in Social Media by ..." (Springer). https://link.springer.com/chapter/10.1007/978-3-031-64193-0_9
9. Numba docs, "Automatic parallelization with @jit". https://numba.pydata.org/numba-doc/dev/user/parallel.html

Original Daley-Kendall (1965) and Maki-Thompson (1973) papers: no free link found, cited via the sources above.
