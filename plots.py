"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

ARTICLE: marks things taken from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1.
Comments without a tag are ours.

File: plots.py
Static plots saved after a headless run.
"""
import textwrap
import numpy as np
import matplotlib
matplotlib.use("Agg")           # we only save pictures here, the live window is separate
import matplotlib.pyplot as plt
from movement import GROUP_NAMES

COLOURS = ["#9aa5b1", "#d62828", "#2a9d8f", "#264653"]   # unaware, spreader, corrector, stifler
NAMES = ["Unaware", "Spreader", "Corrector", "Stifler"]
GROUP_COLOURS = ["#f4a261", "#4361ee", "#9d4edd", "#8d6e63"]


def plotCurve(counts, name, rumour):
    # ARTICLE: infection curve. ours has one line per state
    plt.figure()
    for k in range(4):
        plt.plot(counts[:, k], color=COLOURS[k], label=NAMES[k])
    plt.xlabel("Time")
    plt.ylabel("Agents")
    plt.title("Rumour Curve\n" + textwrap.fill('"' + rumour + '"', 50))
    plt.legend()
    plt.savefig(name, bbox_inches="tight")
    plt.close()


def plotGroupSpreaders(groupCounts, name):
    # spreaders over time per home group, shows how late the rumour reaches each group
    plt.figure()
    plt.plot(groupCounts[:, 0], color="grey", linestyle=":", label="No group")
    for g in range(len(GROUP_NAMES)):
        plt.plot(groupCounts[:, g + 1], color=GROUP_COLOURS[g], label="Group " + GROUP_NAMES[g])
    plt.xlabel("Time")
    plt.ylabel("Spreaders")
    plt.title("Spreaders per group")
    plt.legend()
    plt.savefig(name, bbox_inches="tight")
    plt.close()


def plotTree(agents, name):
    # who told who. one row per hop from patient zero, a line from each agent to whoever told them
    ever = [i for i in range(len(agents)) if agents[i].generation >= 0]
    if len(ever) == 0:
        return
    maxGen = max(agents[i].generation for i in ever)
    pos = {}
    for g in range(maxGen + 1):
        row = [i for i in ever if agents[i].generation == g]
        # order by the parent's position so lines cross less
        row.sort(key=lambda i: pos[agents[i].infector][0] if agents[i].infector in pos else 0)
        for k in range(len(row)):
            pos[row[k]] = ((k + 0.5) / len(row), -g)
    plt.figure(figsize=(10, 5))
    for i in ever:
        p = agents[i].infector
        if p >= 0:
            plt.plot([pos[p][0], pos[i][0]], [pos[p][1], pos[i][1]], color="grey", alpha=0.35, linewidth=0.7)
    for i in ever:
        if agents[i].group >= 0:
            col = GROUP_COLOURS[agents[i].group]
        else:
            col = "black"
        plt.scatter(pos[i][0], pos[i][1], color=col, s=14, zorder=3)
    plt.scatter([pos[i][0] for i in ever if agents[i].infector < 0], [pos[i][1] for i in ever if agents[i].infector < 0],
                color="red", marker="*", s=160, zorder=4, label="Started with it")
    plt.yticks(range(0, -maxGen - 1, -1), ["hop " + str(g) for g in range(maxGen + 1)])
    plt.xticks([])
    plt.title("Who told who (colour = home group, black = no group)")
    plt.legend(loc="lower right")
    plt.savefig(name, bbox_inches="tight")
    plt.close()
