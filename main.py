"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

Comment tags:
    ARTICLE:  from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1
    OUR OWN:  added or changed by us. README reference numbers given where an idea is from research.

File: main.py
Run:
    python main.py                                 live Arcade window, asks for the rumour
    python main.py "rumour text"                   live Arcade window with the rumour given
    python main.py "rumour text" --pygame          the older pygame window instead (needs pygame-ce)
    python main.py "rumour text" --headless        no window, runs and saves the plots (use this for benchmarks)
"""
import os
import sys
from simulation import makeAgents, seedSpreaders, runSimulation, transmissionStats
from plots import plotCurve, plotGroupSpreaders, plotTree

headless = "--headless" in sys.argv
usePygame = "--pygame" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]

# OUR OWN: typed rumour is only a label on the pictures. Benchmarks pass it as an argument.
if len(args) > 0:
    rumour = args[0]
else:
    rumour = input("Type the rumour (enter for default): ").strip()
if rumour == "":
    rumour = "The canteen is closing next week"

# ARTICLE: parameters at the top. OUR OWN: extra settings below.
n = 500
steps = 400
seed = 42
startSpreaders = 1              # one person starts the rumour (patient zero)
startGroup = 0                  # ...in group A
noGroupFraction = 0.2           # OUR OWN: share of agents that belong to no group

settings = {
    "stepSize": 1.5,            # ARTICLE: stepSize
    "contactRadius": 3,         # ARTICLE: infection distance (it used 5 in code, 10 in text)
    "rumourStrength": 0.06,     # OUR OWN: chance scale per contact, found by trial and error
    "correctionStrength": 0.1,  # OUR OWN
    "correctionStart": 60,      # OUR OWN: step the correction starts
    "correctionSeeds": 5,       # OUR OWN
    "leash": 11,                # OUR OWN: how far group members stray from their meeting point
    "travelChance": 0.003,      # OUR OWN: chance per step that a group member starts visiting another group
    "travelSpeed": 2.0,         # OUR OWN
    "stayLength": 40,           # OUR OWN: steps a visitor stays before going home
}


def build():
    # makes a fresh set of agents (the viewer calls this again when R is pressed)
    agents = makeAgents(n, seed, noGroupFraction, settings["leash"])
    return seedSpreaders(agents, startSpreaders, startGroup)


os.makedirs("results", exist_ok=True)
if headless:
    agents = build()
    counts, groupCounts = runSimulation(agents, steps, settings)
    plotCurve(counts, "results/curve.png", rumour)
    plotGroupSpreaders(groupCounts, "results/group_spreaders.png")
    plotTree(agents, "results/tree.png")
    print("final counts [unaware, spreader, corrector, stifler]:", counts[-1])
    print("transmission:", transmissionStats(agents))
else:
    if usePygame:
        from viewer import runViewer            # the older pygame window
    else:
        from viewer_arcade import runViewer     # the Arcade window
    agents, history = runViewer(build, steps, settings, rumour)
    print("stopped at step", len(history), "transmission:", transmissionStats(agents))
