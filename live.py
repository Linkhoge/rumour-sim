"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

Comment tags:
    ARTICLE:  from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1
    OUR OWN:  added or changed by us. README reference numbers given where an idea is from research.

File: live.py
The live simulation window (replaces the article's saved GIF).
Left: all agents moving in one box. Right: counts over time, drawn as it runs.
Close the window to stop.
"""
import textwrap
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from agent import NO_GROUP
from movement import BOX, GROUP_CENTRES, GROUP_NAMES
from simulation import stepSimulation, getPosition, getState, countStates

STATE_COLOURS = ["#9aa5b1", "#d62828", "#2a9d8f", "#264653"]    # unaware, spreader, corrector, stifler
STATE_NAMES = ["Unaware", "Spreader", "Corrector", "Stifler"]
GROUP_COLOURS = ["#f4a261", "#4361ee", "#9d4edd", "#8d6e63"]    # ring colour for each group
STATE_RGBA = np.array([to_rgba(c) for c in STATE_COLOURS])


def buildLive(agents, steps, p, rumour, interval=40):
    n = len(agents)
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 6.2), gridspec_kw={"width_ratios": [1.1, 1]})

    # left: the space. Dashed circles show where each group hangs out.
    ax.set_xlim(0, BOX)
    ax.set_ylim(0, BOX)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for k in range(len(GROUP_CENTRES)):
        c = GROUP_CENTRES[k]
        ax.add_patch(patches.Circle(c, p["leash"], fill=False, linestyle="--", color=GROUP_COLOURS[k]))
        ax.text(c[0], c[1] + p["leash"] + 1.5, "Group " + GROUP_NAMES[k], ha="center",
                fontsize=9, color=GROUP_COLOURS[k])

    # group members: coloured by state, ring colour = group. No group: diamonds, no ring.
    groups = np.array([a.group for a in agents])
    inGroup = np.where(groups != NO_GROUP)[0]
    noGroup = np.where(groups == NO_GROUP)[0]
    rings = [GROUP_COLOURS[g] for g in groups[inGroup]]
    pos = getPosition(agents)
    scG = ax.scatter(pos[inGroup, 0], pos[inGroup, 1], s=30, c=STATE_RGBA[0:1].repeat(len(inGroup), 0),
                     edgecolors=rings, linewidths=1.4)
    scN = ax.scatter(pos[noGroup, 0], pos[noGroup, 1], s=30, marker="D", c=STATE_RGBA[0:1].repeat(len(noGroup), 0),
                     linewidths=0)

    items = [Line2D([0], [0], marker="o", color="w", markerfacecolor=STATE_COLOURS[k], markersize=8,
                    label=STATE_NAMES[k]) for k in range(4)]
    items += [Line2D([0], [0], marker="o", color="w", markerfacecolor="white", markeredgecolor=GROUP_COLOURS[k],
                     markeredgewidth=1.5, markersize=8, label="Group " + GROUP_NAMES[k]) for k in range(4)]
    items.append(Line2D([0], [0], marker="D", color="w", markerfacecolor="grey", markersize=7, label="No group"))
    ax.legend(handles=items, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=5, fontsize=8, frameon=False)

    # right: counts over time (like the article's infection curve, but live)
    history = []
    lines = [ax2.plot([], [], color=STATE_COLOURS[k], label=STATE_NAMES[k])[0] for k in range(4)]
    ax2.set_xlim(0, steps)
    ax2.set_ylim(0, n)
    ax2.set_xlabel("Time")
    ax2.set_ylabel("Agents")
    ax2.legend(loc="center right")
    title = fig.suptitle("", fontsize=11)
    wrapped = textwrap.fill('"' + rumour + '"', 80)

    def update(frame):
        stepSimulation(agents, frame, p)
        pos = getPosition(agents)
        states = np.array(getState(agents))
        scG.set_offsets(pos[inGroup])
        scG.set_facecolor(STATE_RGBA[states[inGroup]])
        scN.set_offsets(pos[noGroup])
        scN.set_facecolor(STATE_RGBA[states[noGroup]])
        history.append(countStates(agents))
        h = np.array(history)
        for k in range(4):
            lines[k].set_data(range(len(h)), h[:, k])
        title.set_text(wrapped + "\nstep " + str(frame) + "   spreaders " + str(h[-1, 1])
                       + "   correctors " + str(h[-1, 2]))
        return scG, scN

    def start():
        return scG, scN             # stops matplotlib running step 0 twice

    anim = FuncAnimation(fig, update, init_func=start, frames=steps, interval=interval, repeat=False, blit=False)
    return fig, anim, history
