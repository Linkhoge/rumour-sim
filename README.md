# Rumour spread simulation - Team Char Siu

Members: Ariel Fajimiyo (more to be added)

Agents move around one shared space and a rumour spreads between them. The rumour is about one agent
(the subject) and it starts with a different agent (patient zero). When it finally reaches the subject
they deny it, and that starts a correction spreading. Serial version first, then a parallel version,
then benchmarks.

## Install
```
pip install -r requirements.txt
pip install --no-deps arcade
```
arcade goes in on its own because it pins an old pymunk that has no wheel for Python 3.14. This worked
for us on Windows with 3.14.

## Run
```
python main.py                            # live window, asks for the rumour text
python main.py "rumour text"              # live window
python main.py "rumour text" --n=200      # fewer agents, easier to watch
python main.py "rumour text" --seed=7     # different seed (default is 42)
python main.py "rumour text" --headless   # no window, saves plots to results/ and prints the run time
```
Same seed, n and settings gives the same run every time. R in the window replays it. Use --headless for
benchmarks, never time the window.

## Reading the window
- The faint circles are where groups A to D hang out. Group members sometimes walk to another group,
  stay a while, then go home.
- Big bright dots with a glow are spreaders (red) and correctors (green). Small dim dots are everyone
  else. Diamonds are agents with no group.
- Arrows: red = rumour passed on, green = correction passed on, grey = heard the rumour but didn't pass it on.
- White ring = patient zero. Pink ring = the subject.
- The gold path is the chain from patient zero to the newest person to catch it. Click an agent to
  trace theirs in white. Hover over an agent for details.
- Keys: space pause, up/down speed, R replay, T keep all arrows, G colour by hop, F follow newest on/off,
  H group rings, esc quit.

States:
- Unaware: hasn't heard it
- Spreader: telling others
- Corrector: spreading the correction
- Stifler: heard it and isn't passing it on any more (timer ran out, or they didn't care)

## Files
- agent.py: Agent class and the states
- movement.py: group meeting points, random walk, visits between groups
- simulation.py: setup, spread rule, one step, headless loop
- viewer_arcade.py: the live window
- plots.py: plots saved after a headless run
- main.py: settings and entry point
- notes.md: technical notes

Comments tagged ARTICLE: come from the article (ref 1). Comments without a tag are ours.

## Todo
- [x] agents, groups, no-group agents, movement, visiting
- [x] rumour about a subject, interest, correction starts from the subject
- [x] live window, headless mode, plots
- [ ] random numbers from (seed, step, agent) so serial and parallel can match
- [ ] numpy array version
- [ ] parallel version (Numba)
- [ ] check serial and parallel give the same result
- [ ] benchmarks (time, speed-up, efficiency)

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
