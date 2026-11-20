"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

Comment tags:
    ARTICLE:  from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1
    OUR OWN:  added or changed by us. README reference numbers given where an idea is from research.

File: viewer.py
Live pygame window. It only draws: it calls stepSimulation() from simulation.py and reads the agents.
Left: the space. Right: counts over time, selected agent info, controls.

Controls:
    SPACE pause     UP / DOWN speed     R restart     T keep all transmission lines (tree)
    G colour by hops from patient zero      CLICK an agent to trace who told who back to patient zero
    ESC or Q quit
"""
import math
import numpy as np
import pygame
from agent import UNAWARE, SPREADER, CORRECTOR, STIFLER, NO_GROUP
from movement import BOX, GROUP_CENTRES, GROUP_NAMES
from simulation import stepSimulation, countStates, transmissionStats

SIM = 700                       # size of the square drawing area in pixels
SIDE = 420                      # width of the side panel
SCALE = SIM / BOX               # pixels per unit
FPS = 30
HOP_LIFE = 70                   # frames a transmission line stays visible (unless tree mode)

BG = (11, 16, 32)
PANEL = (17, 24, 46)
TEXT = (210, 218, 235)
DIM = (120, 130, 155)
STATE_COL = [(92, 102, 125), (255, 77, 77), (46, 214, 170), (96, 125, 200)]     # unaware, spreader, corrector, stifler
STATE_NAMES = ["Unaware", "Spreader", "Corrector", "Stifler"]
GROUP_COL = [(244, 162, 97), (67, 97, 238), (157, 78, 221), (141, 110, 99)]
GEN_COL = [(255, 214, 10), (255, 159, 10), (255, 99, 71), (236, 72, 153),
           (168, 85, 247), (99, 102, 241), (56, 189, 248), (45, 212, 191)]     # hop 0, 1, 2, ...
SPEEDS = [0.25, 0.5, 1, 2, 4, 8]


def toScreen(x, y):
    # y is flipped so "up" on screen is up in the model
    return int(x * SCALE), int((BOX - y) * SCALE)


def wrap(text, width):
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    lines.append(line)
    return lines


def runViewer(build, steps, p, rumour):
    """build() must return a fresh list of agents (used at start and when R is pressed)."""
    pygame.init()
    screen = pygame.display.set_mode((SIM + SIDE, SIM))
    pygame.display.set_caption("Team Char Siu - Rumour Spread")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 14)
    small = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 12)
    big = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 18, bold=True)
    overlay = pygame.Surface((SIM, SIM), pygame.SRCALPHA)

    def text(surf, msg, pos, f=font, col=TEXT):
        surf.blit(f.render(msg, True, col), pos)

    agents = build()
    zeros = [i for i in range(len(agents)) if agents[i].state == SPREADER]    # patient zero(s)
    history = []
    hops = []                       # [x1, y1, x2, y2, born frame, colour]
    t = 0
    frame = 0
    acc = 0.0
    speedIdx = 2
    paused = False
    treeMode = False
    genMode = False
    selected = None
    running = True

    while running:
        # ---------- input ----------
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif e.key == pygame.K_SPACE:
                    paused = not paused
                elif e.key == pygame.K_UP:
                    speedIdx = min(speedIdx + 1, len(SPEEDS) - 1)
                elif e.key == pygame.K_DOWN:
                    speedIdx = max(speedIdx - 1, 0)
                elif e.key == pygame.K_t:
                    treeMode = not treeMode
                elif e.key == pygame.K_g:
                    genMode = not genMode
                elif e.key == pygame.K_r:
                    agents = build()
                    zeros = [i for i in range(len(agents)) if agents[i].state == SPREADER]
                    history, hops, t, acc, selected = [], [], 0, 0.0, None
            elif e.type == pygame.MOUSEBUTTONDOWN and e.pos[0] < SIM:
                best, bestDist = None, 14
                for i in range(len(agents)):
                    sx, sy = toScreen(agents[i].x, agents[i].y)
                    dd = math.hypot(sx - e.pos[0], sy - e.pos[1])
                    if dd < bestDist:
                        best, bestDist = i, dd
                selected = best

        # ---------- simulate ----------
        finished = t >= steps
        if not paused and not finished:
            acc += SPEEDS[speedIdx]
            while acc >= 1 and t < steps:
                acc -= 1
                stepSimulation(agents, t, p)
                for i in range(len(agents)):
                    a = agents[i]
                    if a.changedAt == t:                      # state changed this step: draw the hop
                        if a.state == SPREADER and a.infector >= 0:
                            src, col = agents[a.infector], STATE_COL[SPREADER]
                        elif a.state == CORRECTOR and a.corrSource >= 0:
                            src, col = agents[a.corrSource], STATE_COL[CORRECTOR]
                        else:
                            continue
                        hops.append([src.x, src.y, a.x, a.y, frame, col])
                history.append(countStates(agents))
                t += 1
        if not treeMode:
            hops = [h for h in hops if frame - h[4] < HOP_LIFE]

        # ---------- draw space ----------
        screen.fill(BG)
        overlay.fill((0, 0, 0, 0))
        for k in range(len(GROUP_CENTRES)):                   # group areas
            c = toScreen(*GROUP_CENTRES[k])
            rad = int(p["leash"] * SCALE)
            pygame.draw.circle(overlay, GROUP_COL[k] + (22,), c, rad)
            pygame.draw.circle(overlay, GROUP_COL[k] + (110,), c, rad, 1)
        for h in hops:                                        # transmission lines
            age = frame - h[4]
            alpha = max(70 if treeMode else 0, int(255 * (1 - age / HOP_LIFE)))
            pygame.draw.line(overlay, h[5] + (alpha,), toScreen(h[0], h[1]), toScreen(h[2], h[3]), 2)
        for a in agents:                                      # glow around active spreaders
            if a.state == SPREADER:
                pygame.draw.circle(overlay, STATE_COL[SPREADER] + (45,), toScreen(a.x, a.y), 10)
        screen.blit(overlay, (0, 0))
        for k in range(len(GROUP_CENTRES)):
            c = toScreen(*GROUP_CENTRES[k])
            text(screen, "Group " + GROUP_NAMES[k], (c[0] - 28, c[1] - int(p["leash"] * SCALE) - 18), small, GROUP_COL[k])

        for a in agents:                                      # agents
            pos = toScreen(a.x, a.y)
            if genMode and a.generation >= 0:
                col = GEN_COL[a.generation % len(GEN_COL)]
            else:
                col = STATE_COL[a.state]
            if a.group == NO_GROUP:                           # no group: diamond
                pts = [(pos[0], pos[1] - 5), (pos[0] + 5, pos[1]), (pos[0], pos[1] + 5), (pos[0] - 5, pos[1])]
                pygame.draw.polygon(screen, col, pts)
            else:
                pygame.draw.circle(screen, col, pos, 4)
                pygame.draw.circle(screen, GROUP_COL[a.group], pos, 5, 1)

        for z in zeros:                                       # patient zero marker
            pos = toScreen(agents[z].x, agents[z].y)
            pulse = 11 + int(3 * math.sin(frame * 0.15))
            pygame.draw.circle(screen, (255, 255, 255), pos, pulse, 2)
            text(screen, "Patient 0" if len(zeros) == 1 else "P0", (pos[0] + 14, pos[1] - 18), small)

        if selected is not None:                              # trace back to patient zero
            chain, i, guard = [], selected, 0
            while i >= 0 and guard < 500:
                chain.append(i)
                i = agents[i].infector
                guard += 1
            pts = [toScreen(agents[j].x, agents[j].y) for j in chain]
            if len(pts) > 1:
                pygame.draw.lines(screen, (255, 255, 255), False, pts, 2)
            sp = toScreen(agents[selected].x, agents[selected].y)
            pygame.draw.circle(screen, (255, 255, 255), sp, 9, 2)

        # ---------- side panel ----------
        pygame.draw.rect(screen, PANEL, (SIM, 0, SIDE, SIM))
        x0 = SIM + 20
        text(screen, "Team Char Siu - Rumour Spread", (x0, 14), big)
        y = 46
        for line in wrap('"' + rumour + '"', 44):
            text(screen, line, (x0, y), font, (255, 214, 10))
            y += 18
        y += 6
        counts = countStates(agents)
        text(screen, "step " + str(t) + " / " + str(steps) + ("   PAUSED" if paused else "")
             + ("   FINISHED (R to restart)" if finished else ""), (x0, y))
        y += 22
        for k in range(4):
            pygame.draw.circle(screen, STATE_COL[k], (x0 + 6, y + 8), 5)
            text(screen, STATE_NAMES[k] + ": " + str(counts[k]), (x0 + 20, y))
            y += 18
        stats = transmissionStats(agents)
        y += 4
        text(screen, "Hops from patient 0 so far: " + str(stats["maxGeneration"]), (x0, y), font, DIM)
        y += 18
        text(screen, "Had the rumour: " + str(stats["everHadRumour"]), (x0, y), font, DIM)
        y += 28

        # live chart
        cx, cy, cw, ch = x0, y, SIDE - 40, 170
        pygame.draw.rect(screen, (24, 32, 60), (cx, cy, cw, ch))
        pygame.draw.rect(screen, (60, 72, 110), (cx, cy, cw, ch), 1)
        if len(history) > 1:
            hist = np.array(history)
            for k in range(4):
                pts = [(cx + int(j / steps * cw), cy + ch - int(hist[j, k] / len(agents) * ch))
                       for j in range(len(hist))]
                pygame.draw.lines(screen, STATE_COL[k], False, pts, 2)
        text(screen, "counts over time", (cx + 6, cy + 4), small, DIM)
        y = cy + ch + 14

        if selected is not None:
            a = agents[selected]
            text(screen, "Selected agent " + str(selected), (x0, y), font, (255, 255, 255))
            y += 18
            grp = "no group" if a.group == NO_GROUP else "group " + GROUP_NAMES[a.group]
            text(screen, STATE_NAMES[a.state] + ", " + grp, (x0, y), small)
            y += 16
            if a.generation >= 0:
                told = "started it" if a.infector < 0 else "told by agent " + str(a.infector)
                text(screen, "hop " + str(a.generation) + ", " + told, (x0, y), small)
            else:
                text(screen, "has not had the rumour", (x0, y), small)
            y += 22
        else:
            text(screen, "click an agent to trace who told who", (x0, y), small, DIM)
            y += 22

        help_ = ["SPACE pause  UP/DOWN speed " + str(SPEEDS[speedIdx]) + "x", "R restart",
                 "T tree lines: " + ("ON" if treeMode else "off"),
                 "G colour by hop: " + ("ON" if genMode else "off"), "ESC quit"]
        for line in help_:
            text(screen, line, (x0, y), small, DIM)
            y += 15
        text(screen, "ring = home group, diamond = no group", (x0, SIM - 20), small, DIM)

        pygame.display.flip()
        clock.tick(FPS)
        frame += 1

    pygame.quit()
    return agents, history
