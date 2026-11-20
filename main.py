"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

Comment tags:
    ARTICLE:  from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1
    Comments without a tag are ours. README reference numbers are given where an idea is from research.

File: main.py
Run:
    python main.py                                 live Arcade window, asks for the rumour
    python main.py "rumour text"                   live Arcade window with the rumour given
    python main.py "rumour text" --n=200           fewer agents (nicer to watch)
    python main.py "rumour text" --seed=7          use a different seed (the default is 42)
    python main.py "rumour text" --pygame          the older pygame window instead (needs pygame-ce)
    python main.py "rumour text" --headless        no window, saves plots and prints the run time (use for benchmarks)

One seed decides the whole run, so the same seed, n and settings always give exactly the same run.
In the live window, R replays the same run.
"""
import os
import sys
import time
from simulation import makeAgents, seedSpreaders, pickSubject, runSimulation, transmissionStats
from plots import plotCurve, plotGroupSpreaders, plotTree

headless = "--headless" in sys.argv
usePygame = "--pygame" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]

# the typed rumour is only a label on the pictures. Benchmarks pass it as an argument.
if len(args) > 0:
    rumour = args[0]
else:
    rumour = input("Type the rumour (enter for default): ").strip()
if rumour == "":
    rumour = "The canteen is closing next week"

# ARTICLE: parameters at the top. Extra settings below.
n = 500
seed = 42
for a in sys.argv[1:]:
    if a.startswith("--n="):
        n = int(a[4:])                  # number of agents from the command line
    if a.startswith("--seed="):
        seed = int(a[7:])               # a different seed gives a different (but repeatable) run
steps = 400
startSpreaders = 1              # one person starts the rumour (patient zero)
startGroup = 0                  # ...in group A
subjectGroup = 3                # the rumour is ABOUT someone in group D (the far corner from group A)
noGroupFraction = 0.2           # share of agents that belong to no group

settings = {
    "stepSize": 1.5,            # ARTICLE: stepSize
    "contactRadius": 4 * (500 / n) ** 0.5,   # scaled with n so each agent meets about as many people
    "rumourStrength": 0.06,     # chance scale per contact, found by trial and error
    "correctionStrength": 0.1,
    "correctionStart": 60,      # step the extra correctors appear (only if correctionSeeds > 0)
    "correctionSeeds": 0,       # 0 = the only correction comes from the subject denying it
    "minInterest": 0.3,         # lowest chance someone who hears it passes it on (1.0 = everyone does)
    "subjectDenies": 1.0,       # chance the subject denies it when they hear it (otherwise they shrug)
    "leash": 15,                # how far group members stray from their meeting point
    "travelChance": 0.003,      # chance per step that a group member starts visiting another group
    "travelSpeed": 2.0,
    "stayLength": 40,           # steps a visitor stays before going home
}


def build():
    # makes a fresh set of agents from the seed (the viewer calls this again when R is pressed)
    agents = makeAgents(n, seed, noGroupFraction, settings["leash"])
    agents = seedSpreaders(agents, startSpreaders, startGroup)
    return pickSubject(agents, subjectGroup)


os.makedirs("results", exist_ok=True)
if headless:
    agents = build()
    start = time.perf_counter()
    counts, groupCounts = runSimulation(agents, steps, settings)
    seconds = time.perf_counter() - start
    plotCurve(counts, "results/curve.png", rumour)
    plotGroupSpreaders(groupCounts, "results/group_spreaders.png")
    plotTree(agents, "results/tree.png")
    print("seed:", seed, "  n:", n, "  steps:", steps)
    print("final counts [unaware, spreader, corrector, stifler]:", counts[-1])
    print("transmission:", transmissionStats(agents))
    print("run time: %.2f s" % seconds)
else:
    if usePygame:
        from viewer import runViewer            # the older pygame window
    else:
        from viewer_arcade import runViewer     # the Arcade window
    agents, history = runViewer(build, steps, settings, rumour)
    print("stopped at step", len(history), "transmission:", transmissionStats(agents))
