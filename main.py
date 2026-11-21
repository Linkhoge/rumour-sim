"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

ARTICLE: marks things taken from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1.
Comments without a tag are ours.

File: main.py
Run:
    python main.py                                 live window, asks for the rumour
    python main.py "rumour text"                   live window with the rumour given
    python main.py "rumour text" --n=200           fewer agents, easier to watch
    python main.py "rumour text" --seed=7          different seed (default is 42)
    python main.py "rumour text" --headless        no window, saves plots and prints the run time (use for benchmarks)

One seed decides the whole run, so same seed + n + settings = same run. R in the live window replays it.
"""
import os
import sys
import time
from simulation import makeAgents, seedSpreaders, pickSubject, runSimulation, transmissionStats
from plots import plotCurve, plotGroupSpreaders, plotNearSubject, plotTree

headless = "--headless" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]

# the typed rumour is just a label on the pictures
if len(args) > 0:
    rumour = args[0]
else:
    rumour = input("Type the rumour (enter for default): ").strip()
if rumour == "":
    rumour = "The canteen is closing next week"

# ARTICLE: settings at the top, our extras below
n = 500
seed = 42
for a in sys.argv[1:]:
    if a.startswith("--n="):
        n = int(a[4:])                  # number of agents
    if a.startswith("--seed="):
        seed = int(a[7:])               # different seed, different run, but repeatable
steps = 400
startSpreaders = 1              # one person starts the rumour (patient zero)
startGroup = 0                  # in group A
subjectGroup = 3                # the rumour is about someone in group D, the far corner from group A
noGroupFraction = 0.2           # share of agents with no group

settings = {
    "stepSize": 1.5,            # ARTICLE: stepSize
    "contactRadius": 4 * (500 / n) ** 0.5,   # scaled with n so agents meet about the same number of people
    "rumourStrength": 0.06,     # found by trial and error
    "correctionStrength": 0.03, # low on purpose: only a small pool of correctors
    "correctionStart": 60,      # only used if correctionSeeds > 0
    "correctionSeeds": 0,       # 0 = the only correction comes from the subject
    "minInterest": 0.5,         # lowest chance someone who hears it believes it, so about 75% believe it on average
    "subjectDenies": 1.0,       # chance the subject denies it when they hear it
    "avoidRadius": 7,           # believers keep this far from the subject (0 turns avoiding off)
    "avoidSpeed": 1.5,          # how far a believer is pushed away per step
    "avoidChance": 0.8,         # chance per step that a believer close to the subject moves away
    "noticeAfter": 20,          # the subject realises something is up after this many close believers
    "nearRadius": 10,           # how close counts as "near the subject" for the isolation numbers
    "leash": 15,                # how far group members stray from their meeting point
    "travelChance": 0.003,      # chance per step a group member starts visiting another group
    "travelSpeed": 2.0,
    "stayLength": 40,           # steps a visitor stays
}


def build():
    # fresh agents from the seed (R in the viewer calls this again)
    agents = makeAgents(n, seed, noGroupFraction, settings["leash"])
    agents = seedSpreaders(agents, startSpreaders, startGroup)
    return pickSubject(agents, subjectGroup)


os.makedirs("results", exist_ok=True)
if headless:
    agents = build()
    start = time.perf_counter()
    counts, groupCounts, near = runSimulation(agents, steps, settings)
    seconds = time.perf_counter() - start
    stats = transmissionStats(agents)
    plotCurve(counts, "results/curve.png", rumour)
    plotGroupSpreaders(groupCounts, "results/group_spreaders.png")
    plotNearSubject(near, "results/near_subject.png", stats["subjectHeardAtStep"], settings["nearRadius"])
    plotTree(agents, "results/tree.png")
    print("seed:", seed, "  n:", n, "  steps:", steps)
    print("final counts [unaware, spreader, corrector, stifler]:", counts[-1])
    print("transmission:", stats)
    print("run time: %.2f s" % seconds)
else:
    from viewer_arcade import runViewer         # only needed for the live window
    agents, history = runViewer(build, steps, settings, rumour)
    print("stopped at step", len(history), "transmission:", transmissionStats(agents))
