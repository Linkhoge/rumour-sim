"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

ARTICLE: marks things taken from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1.
Comments without a tag are ours.

File: viewer_arcade.py
The live window, made with Arcade. It only draws things. It calls stepSimulation() and reads the
agents, so it doesn't change the model.

Intro: for the first few seconds patient zero and the subject are drawn together in the middle, then
they glide to their real places in their groups and the simulation starts. This is only how it is drawn,
the model is not touched. ENTER skips it, R plays it again.

Following who told who:
    - spreaders and correctors are big and bright with a glow, everyone else is small and dim
    - when someone passes it on there's an arrow from the teller to the new person and a ring pulses
      on them. arrows fade after about 5 seconds (T keeps them)
    - dots grow with how many people they told, so the big ones are the superspreaders (S turns this on/off).
      the top 3 are labelled and the top 5 are listed on the right
    - the gold path is the chain from patient zero to the newest person to catch it (numbers are hops).
      click an agent to trace theirs instead (white)
    - hover over an agent to see its details, including its interest and gullibility
    - the list on the right names the agents (#id -> #id)

Controls:
    SPACE pause   UP/DOWN speed   R replay   ENTER skip the intro   ESC or Q quit
    S size dots by how many people they told   T keep arrows   G colour by hop
    F follow newest on/off   H group rings on/off
    CLICK an agent to trace who told them
"""
import math
import numpy as np
import arcade
from agent import UNAWARE, SPREADER, CORRECTOR, STIFLER, NO_GROUP
from movement import BOX, GROUP_CENTRES, GROUP_NAMES
from simulation import stepSimulation, countStates, transmissionStats

SIM = 700                       # size of the square drawing area in pixels
SIDE = 440                      # width of the side panel
SCALE = SIM / BOX               # pixels per unit
TICKS_PER_SECOND = 30           # model steps per second at 1x speed
SMOOTH_RATE = 14                # higher = drawn positions catch up faster, lower = smoother
ARROW_LIFE = 5.0                # seconds an arrow stays (unless T)
PULSE_LIFE = 1.0                # seconds the ring on a new person pulses
FONT = ("Consolas", "Menlo", "DejaVu Sans Mono", "Courier New")

INTRO_HOLD = 3.0                # seconds patient zero and the subject stay together in the middle
INTRO_GLIDE = 2.0               # seconds they take to glide to their groups (the simulation starts after this)
INTRO_GAP = 5                   # how far apart they are in the middle, in box units

# how the agents look, change these if you want
GLOW_RADIUS = 11                # size of the glow around spreaders and correctors
GLOW_ALPHA = 120                # 0 to 255, how strong the glow is
DOT_ACTIVE = 5                  # radius of a spreader or corrector
DOT_IDLE = 2.5                  # radius of everyone else
DOT_HOP = 4                     # radius when colouring by hop (G)
PULSE_SIZE = 18                 # how far the ring on a new person grows
SPREAD_BASE = 3                 # superspreader view: radius of someone who told 1 person is about this + SPREAD_GROW
SPREAD_GROW = 3                 # radius grows with the square root of how many people they told
SPREAD_MAX = 16                 # biggest radius a dot can get in this view
CHART_HEIGHT = 140              # height of the counts-over-time chart in pixels

BG = (11, 16, 32)
PANEL = (17, 24, 46)
TEXT = (210, 218, 235)
DIM = (120, 130, 155)
GOLD = (255, 214, 10)
WHITE = (255, 255, 255)
IGNORED_COL = (150, 160, 185)   # arrow to someone who heard it but didn't pass it on
SUBJECT_COL = (255, 105, 180)   # ring around the subject
SPREAD_COL = (255, 159, 10)     # someone who told people but has stopped spreading (superspreader view)
# unaware and stiflers are dim on purpose so the spreaders stand out
STATE_COL = [(58, 66, 92), (255, 77, 77), (46, 214, 170), (78, 92, 128)]       # unaware, spreader, corrector, stifler
LINE_COL = [(130, 145, 180), (255, 77, 77), (46, 214, 170), (130, 145, 180)]   # brighter versions for the panel
STATE_NAMES = ["Unaware", "Spreader", "Corrector", "Stifler"]
STATE_HELP = ["hasn't heard it", "telling others", "spreading the correction", "heard it, stopped passing it on"]
GROUP_COL = [(244, 162, 97), (67, 97, 238), (157, 78, 221), (141, 110, 99)]
GEN_COL = [(255, 214, 10), (255, 159, 10), (255, 99, 71), (236, 72, 153),
           (168, 85, 247), (99, 102, 241), (56, 189, 248), (45, 212, 191)]     # hop 0, 1, 2, ...
SPEEDS = [0.25, 0.5, 1, 2, 4, 8]


def rgba(col, alpha):
    return (col[0], col[1], col[2], alpha)


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


def drawArrow(p1, p2, col, width):
    # line from p1 to p2 with a small arrow head at p2 (the person who just heard it)
    arcade.draw_line(p1[0], p1[1], p2[0], p2[1], col, width)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    size = 9
    lx, ly = p2[0] - size * math.cos(ang - 0.45), p2[1] - size * math.sin(ang - 0.45)
    rx, ry = p2[0] - size * math.cos(ang + 0.45), p2[1] - size * math.sin(ang + 0.45)
    arcade.draw_triangle_filled(p2[0], p2[1], lx, ly, rx, ry, col)


def traceChain(agents, idx):
    # follow the told-by links back to patient zero. returns [patient zero, ..., idx]
    chain, guard = [], 0
    while idx >= 0 and guard < 500:
        chain.append(idx)
        idx = agents[idx].infector
        guard += 1
    return chain[::-1]


def describe(agents, i, p):
    # lines of text about one agent (hover popup and side panel)
    a = agents[i]
    grp = "no group" if a.group == NO_GROUP else "group " + GROUP_NAMES[a.group]
    lines = ["#" + str(i) + "  " + STATE_NAMES[a.state] + ", " + grp]
    if a.isSubject:
        lines.append("the rumour is about this agent")
    if a.generation >= 0:
        lines.append("hop " + str(a.generation) + (", started it" if a.infector < 0 else ", told by #" + str(a.infector)))
        if a.ignored:
            lines.append("heard it but didn't pass it on")
    else:
        lines.append("has not had the rumour")
    if a.corrGeneration >= 0:
        lines.append("started the correction" if a.corrSource < 0 else "heard the correction from #" + str(a.corrSource))
    # their traits, to see why they did or didn't pass it on
    lines.append("interest " + format(a.interest, ".2f") + "   gullibility " + format(a.gullibility, ".2f"))
    if not a.isSubject:
        minI = p.get("minInterest", 1.0)
        lines.append("chance to pass it on: " + str(int(round(100 * (minI + (1 - minI) * a.interest)))) + "%")
    return lines


class RumourWindow(arcade.Window):
    def __init__(self, build, steps, p, rumour):
        super().__init__(SIM + SIDE, SIM, "Team Char Siu - Rumour Spread", vsync=True, antialiasing=True)
        self.background_color = BG
        self.build = build
        self.steps = steps
        self.p = p
        self.rumour = rumour
        self.texts = {}                 # Text objects, made once and reused (much faster than draw_text)
        self.speedIdx = 1               # start slow (0.5x) so it's easy to follow
        self.paused = False
        self.treeMode = False
        self.genMode = False
        self.spreadMode = True          # superspreader view, on by default
        self.follow = True
        self.rings = False
        self.mousePos = (-1000, -1000)
        self.now = 0.0
        self.newRun()

    def newRun(self):
        self.agents = self.build()
        n = len(self.agents)
        self.zeros = [i for i in range(n) if self.agents[i].state == SPREADER]    # patient zero
        self.shown = self.realPositions()
        self.history = []
        self.arrows = []                # [x1, y1, x2, y2, born time, colour] in pixels
        self.pulses = []                # [agent index, born time, colour]
        self.log = []                   # latest passes: (step, from, to, hop, kind)
        self.latest = -1                # most recent agent to catch the rumour
        self.told = [0] * n             # how many people each agent has told
        self.top = []                   # the agents who told the most people, biggest first
        self.t = 0
        self.acc = 0.0
        self.selected = None
        # intro: patient zero and the subject are drawn together in the middle until the intro is over
        self.intro = 0.0                # seconds into the intro
        mid = BOX / 2
        self.introPos = {}
        for j, i in enumerate(self.zeros):
            self.introPos[i] = (mid - INTRO_GAP - 2 * j, mid)
        for i in range(n):
            if self.agents[i].isSubject:
                self.introPos[i] = (mid + INTRO_GAP, mid)
        for i, pos in self.introPos.items():
            self.shown[i] = pos
        # one glow and one dot sprite per agent. the glow is drawn additive
        self.glowList = arcade.SpriteList()
        self.dotList = arcade.SpriteList()
        self.glows, self.dots = [], []
        self.dotStyle = [None] * n
        self.glowStyle = [None] * n
        for a in self.agents:
            g = arcade.SpriteCircle(GLOW_RADIUS, (255, 255, 255, 255), soft=True)
            g.color = (255, 255, 255, 0)
            self.glowList.append(g)
            self.glows.append(g)
            if a.group == NO_GROUP:                       # no group: diamond (square turned 45 degrees)
                dot = arcade.SpriteSolidColor(10, 10, color=(255, 255, 255, 255))
                dot.angle = 45
            else:
                dot = arcade.SpriteCircle(8, (255, 255, 255, 255))
            self.dotList.append(dot)
            self.dots.append(dot)

    def realPositions(self):
        return np.array([[a.x, a.y] for a in self.agents], dtype=float)

    def toScreen(self, pos):
        return pos[0] * SCALE, pos[1] * SCALE

    def nearestAgent(self, mouse, maxDist):
        best, bestDist = None, maxDist
        for i in range(len(self.agents)):
            sx, sy = self.toScreen(self.shown[i])
            dd = math.hypot(sx - mouse[0], sy - mouse[1])
            if dd < bestDist:
                best, bestDist = i, dd
        return best

    # ---------------- input ----------------
    def on_key_press(self, symbol, modifiers):
        k = arcade.key
        if symbol == k.ESCAPE or symbol == k.Q:
            self.close()
        elif symbol == k.SPACE:
            self.paused = not self.paused
        elif symbol == k.ENTER:
            self.intro = INTRO_HOLD + INTRO_GLIDE         # skip the intro
        elif symbol == k.UP:
            self.speedIdx = min(self.speedIdx + 1, len(SPEEDS) - 1)
        elif symbol == k.DOWN:
            self.speedIdx = max(self.speedIdx - 1, 0)
        elif symbol == k.T:
            self.treeMode = not self.treeMode
        elif symbol == k.G:
            self.genMode = not self.genMode
        elif symbol == k.S:
            self.spreadMode = not self.spreadMode
        elif symbol == k.F:
            self.follow = not self.follow
        elif symbol == k.H:
            self.rings = not self.rings
        elif symbol == k.R:
            self.newRun()

    def on_mouse_motion(self, x, y, dx, dy):
        self.mousePos = (x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if x < SIM:
            self.selected = self.nearestAgent((x, y), 16)

    # ---------------- update ----------------
    def on_update(self, delta_time):
        dt = min(delta_time, 0.05)
        self.now += dt
        introTotal = INTRO_HOLD + INTRO_GLIDE
        intro = self.intro < introTotal                   # the simulation waits until the intro is over
        if intro:
            self.intro += dt
        events = []
        finished = self.t >= self.steps
        if not self.paused and not finished and not intro:
            self.acc += dt * TICKS_PER_SECOND * SPEEDS[self.speedIdx]
            while self.acc >= 1 and self.t < self.steps:
                self.acc -= 1
                stepSimulation(self.agents, self.t, self.p)
                for i in range(len(self.agents)):
                    a = self.agents[i]
                    if a.changedAt == self.t:             # state changed this step: someone told them
                        if a.heardAt == self.t and a.infector >= 0:       # heard the rumour this step
                            kind = "ignored" if a.ignored else "rumour"
                            col = IGNORED_COL if a.ignored else STATE_COL[SPREADER]
                            events.append((a.infector, i, col, kind, a.generation, self.t))
                            if not a.ignored:
                                self.latest = i
                        elif a.state == CORRECTOR and a.corrSource >= 0:
                            events.append((a.corrSource, i, STATE_COL[CORRECTOR], "correction", a.corrGeneration, self.t))
                self.history.append(countStates(self.agents))
                self.t += 1

        # how many people each agent has told (from the told-by links), and who told the most
        told = [0] * len(self.agents)
        for a in self.agents:
            if a.infector >= 0:
                told[a.infector] += 1
        self.told = told
        order = sorted(range(len(told)), key=lambda i: -told[i])
        self.top = [i for i in order[:5] if told[i] > 0]

        # drawn positions ease towards the real ones, this is what stops the jitter
        k = 1 - math.exp(-dt * SMOOTH_RATE)
        real = self.realPositions()
        self.shown += (real - self.shown) * k
        if self.intro < introTotal:                       # intro: hold in the middle, then glide to their groups
            u = max(0.0, (self.intro - INTRO_HOLD) / INTRO_GLIDE)
            e = u * u * (3 - 2 * u)                       # slow start, slow finish
            for i, (ix, iy) in self.introPos.items():
                self.shown[i] = (ix + (real[i][0] - ix) * e, iy + (real[i][1] - iy) * e)

        for src, i, col, kind, hop, tt in events:
            x1, y1 = self.toScreen(self.shown[src])
            x2, y2 = self.toScreen(self.shown[i])
            self.arrows.append([x1, y1, x2, y2, self.now, col])
            self.pulses.append([i, self.now, col])
            self.log.append((tt, src, i, hop, kind))
        if not self.treeMode:
            self.arrows = [h for h in self.arrows if self.now - h[4] < ARROW_LIFE]
        self.pulses = [q for q in self.pulses if self.now - q[1] < PULSE_LIFE]
        self.log = self.log[-60:]

        # sprites: position every frame, colour and size only when they change
        for i in range(len(self.agents)):
            a = self.agents[i]
            sx, sy = self.toScreen(self.shown[i])
            active = a.state == SPREADER or a.state == CORRECTOR
            if self.genMode and a.generation >= 0:
                col, rad = GEN_COL[a.generation % len(GEN_COL)], DOT_HOP
            else:
                col, rad = STATE_COL[a.state], (DOT_ACTIVE if active else DOT_IDLE)
            if self.spreadMode and self.told[i] > 0:
                # superspreader view: bigger the more people they told. ones who have stopped spreading go orange
                rad = max(rad, min(SPREAD_MAX, SPREAD_BASE + SPREAD_GROW * math.sqrt(self.told[i])))
                if not active and not self.genMode:
                    col = SPREAD_COL
            dot = self.dots[i]
            dot.position = (sx, sy)
            if self.dotStyle[i] != (col, rad):
                self.dotStyle[i] = (col, rad)
                dot.color = rgba(col, 255)
                dot.scale = (rad * 1.5 / 10) if a.group == NO_GROUP else (rad / 8)
            glow = self.glows[i]
            glow.position = (sx, sy)
            if active:
                glow.color = rgba(STATE_COL[a.state], GLOW_ALPHA)
                glow.scale = 0.85 + 0.15 * math.sin(self.now * 6 + i)
                self.glowStyle[i] = True
            elif self.glowStyle[i]:
                glow.color = (255, 255, 255, 0)
                self.glowStyle[i] = False

    # ---------------- drawing ----------------
    def label(self, key, msg, x, ytop, col=TEXT, size=11, bold=False):
        # ytop = distance from the top of the window, easier for laying out the panel
        y = SIM - ytop
        t = self.texts.get(key)
        if t is None:
            t = arcade.Text(msg, x, y, col, size, font_name=FONT, bold=bold, anchor_y="top")
            self.texts[key] = t
        else:
            if t.text != msg:
                t.text = msg
            t.position = (x, y)
            if tuple(t.color) != tuple(rgba(col, 255)):
                t.color = rgba(col, 255)
        t.draw()

    def on_draw(self):
        self.clear()
        p = self.p
        rad = p["leash"] * SCALE
        for k in range(len(GROUP_CENTRES)):                   # group areas, faint
            cx, cy = GROUP_CENTRES[k][0] * SCALE, GROUP_CENTRES[k][1] * SCALE
            arcade.draw_circle_filled(cx, cy, rad, rgba(GROUP_COL[k], 20))
            arcade.draw_circle_outline(cx, cy, rad, rgba(GROUP_COL[k], 90), 1)

        self.glowList.draw(blend_function=self.ctx.BLEND_PREMULTIPLIED_ALPHA)   # soft glow, additive

        for h in self.arrows:                                 # arrows from teller to new person
            age = self.now - h[4]
            alpha = max(90 if self.treeMode else 0, int(255 * (1 - age / ARROW_LIFE)))
            drawArrow((h[0], h[1]), (h[2], h[3]), rgba(h[5], alpha), 3)
        for q in self.pulses:                                 # ring that follows the new person
            age = self.now - q[1]
            x, y = self.toScreen(self.shown[q[0]])
            arcade.draw_circle_outline(x, y, 5 + PULSE_SIZE * age / PULSE_LIFE,
                                       rgba(q[2], int(255 * (1 - age / PULSE_LIFE))), 2)

        self.dotList.draw()                                   # agents

        if self.rings:
            for i in range(len(self.agents)):
                if self.agents[i].group != NO_GROUP:
                    x, y = self.toScreen(self.shown[i])
                    arcade.draw_circle_outline(x, y, self.dotStyle[i][1] + 2 if self.dotStyle[i] else 5,
                                               GROUP_COL[self.agents[i].group], 1)

        # gold path from patient zero to the newest person (white if you clicked an agent)
        target = self.selected if self.selected is not None else (self.latest if self.follow else -1)
        if target >= 0:
            chain = traceChain(self.agents, target)
            col = WHITE if self.selected is not None else GOLD
            pts = [self.toScreen(self.shown[j]) for j in chain]
            for k in range(len(pts) - 1):
                drawArrow(pts[k], pts[k + 1], col, 3)
            for k in range(len(pts)):
                arcade.draw_circle_outline(pts[k][0], pts[k][1], 9, col, 2)
                if self.agents[chain[k]].generation >= 0:
                    self.label("hop" + str(k), str(self.agents[chain[k]].generation),
                               pts[k][0] + 8, SIM - pts[k][1] - 4, col, 10)

        for n, z in enumerate(self.zeros):                    # patient zero marker
            x, y = self.toScreen(self.shown[z])
            arcade.draw_circle_outline(x, y, 12 + 3 * math.sin(self.now * 4.5), WHITE, 2)
            self.label("p0_" + str(n), "PATIENT 0" if len(self.zeros) == 1 else "P0", x - 4, SIM - y - 18, WHITE, 10, True)

        for i in range(len(self.agents)):                     # subject marker
            if self.agents[i].isSubject:
                x, y = self.toScreen(self.shown[i])
                arcade.draw_circle_outline(x, y, 14, SUBJECT_COL, 2)
                self.label("subject", "SUBJECT", x - 4, SIM - y - 20, SUBJECT_COL, 10, True)

        if self.intro < INTRO_HOLD:                           # captions while they are together in the middle
            cx, cy = (BOX / 2) * SCALE, (BOX / 2) * SCALE
            self.label("intro0", "PATIENT 0 starts the rumour", cx - 110, SIM - cy + 30, WHITE, 11, True)
            self.label("intro1", "the SUBJECT is who it's about", cx - 110, SIM - cy + 48, SUBJECT_COL, 11, True)
            self.label("intro2", "press ENTER to skip", cx - 110, SIM - cy + 68, DIM, 10)

        if self.spreadMode:                                   # label the top 3 spreaders, gold ring on the biggest
            for r, i in enumerate(self.top[:3]):
                x, y = self.toScreen(self.shown[i])
                if r == 0:
                    arcade.draw_circle_outline(x, y, SPREAD_MAX + 4, GOLD, 2)
                self.label("top" + str(r), "#" + str(i) + " told " + str(self.told[i]),
                           x + 12, SIM - y - 4, GOLD if r == 0 else TEXT, 10, r == 0)

        for k in range(len(GROUP_CENTRES)):                   # group names
            cx, cy = GROUP_CENTRES[k][0] * SCALE, GROUP_CENTRES[k][1] * SCALE
            self.label("grp" + str(k), "Group " + GROUP_NAMES[k], cx - 28, SIM - (cy + rad + 4), GROUP_COL[k], 10)

        self.drawTooltip()
        self.drawPanel()

    def drawTooltip(self):
        mx, my = self.mousePos
        if mx >= SIM or mx < 0:
            return
        hv = self.nearestAgent(self.mousePos, 12)
        if hv is None:
            return
        lines = describe(self.agents, hv, self.p)
        w = max(len(s) for s in lines) * 7 + 14
        h = 16 * len(lines) + 8
        bx = min(mx + 14, SIM - w - 4)
        by = min(my + 8, SIM - h - 4)
        arcade.draw_lbwh_rectangle_filled(bx, by, w, h, (30, 40, 75, 235))
        arcade.draw_lbwh_rectangle_outline(bx, by, w, h, (130, 145, 180), 1)
        for k in range(len(lines)):
            self.label("tip" + str(k), lines[k], bx + 7, SIM - (by + h - 5 - 16 * k), TEXT, 10)

    def drawPanel(self):
        p = self.p
        arcade.draw_lbwh_rectangle_filled(SIM, 0, SIDE, SIM, PANEL)
        x0 = SIM + 20
        self.label("title", "Team Char Siu - Rumour Spread", x0, 10, TEXT, 14, True)
        y = 38
        for k, line in enumerate(wrap('"' + self.rumour + '"', 50)[:2]):
            self.label("rumour" + str(k), line, x0, y, GOLD, 11)
            y += 17
        y += 4
        finished = self.t >= self.steps
        self.label("step", "step " + str(self.t) + " / " + str(self.steps) + "   " + str(SPEEDS[self.speedIdx]) + "x"
                   + ("   PAUSED" if self.paused else "") + ("   FINISHED (R replays)" if finished else "")
                   + ("   INTRO" if self.intro < INTRO_HOLD + INTRO_GLIDE else ""), x0, y)
        y += 22
        counts = countStates(self.agents)
        stats = transmissionStats(self.agents)
        for k in range(4):
            arcade.draw_circle_filled(x0 + 6, SIM - (y + 8), 5, LINE_COL[k])
            self.label("count" + str(k), STATE_NAMES[k] + ": " + str(counts[k]) + "  (" + STATE_HELP[k] + ")", x0 + 20, y)
            y += 18
        self.label("stats", "had the rumour: " + str(stats["everHadRumour"]) + "   ignored it: "
                   + str(stats["ignoredIt"]), x0, y, DIM, 10)
        y += 22

        cw, ch = SIDE - 40, CHART_HEIGHT                      # live chart
        bottom = SIM - (y + ch)
        arcade.draw_lbwh_rectangle_filled(x0, bottom, cw, ch, (24, 32, 60))
        arcade.draw_lbwh_rectangle_outline(x0, bottom, cw, ch, (60, 72, 110), 1)
        if len(self.history) > 1:
            hist = np.array(self.history)
            for k in range(4):
                pts = [(x0 + j / self.steps * cw, bottom + hist[j, k] / len(self.agents) * ch)
                       for j in range(len(hist))]
                arcade.draw_line_strip(pts, LINE_COL[k], 2)
        self.label("chart", "counts over time", x0 + 6, y + 4, DIM, 10)
        y += ch + 10

        self.label("topTitle", "top spreaders (told the most people)", x0, y, DIM, 10)
        y += 16
        if len(self.top) == 0:
            self.label("topNone", "nobody has passed it on yet", x0, y, DIM, 10)
            y += 14
        for k, i in enumerate(self.top[:5]):
            a = self.agents[i]
            grp = "no group" if a.group == NO_GROUP else "group " + GROUP_NAMES[a.group]
            self.label("topRow" + str(k), "#" + str(i) + "  told " + str(self.told[i]) + "   " + grp,
                       x0, y, GOLD if k == 0 else TEXT, 10)
            y += 14
        y += 10

        self.label("logTitle", "latest passes (teller -> new person)", x0, y, DIM, 10)
        y += 16
        for k, entry in enumerate(self.log[::-1][:5]):
            col = LINE_COL[SPREADER] if entry[4] == "rumour" else LINE_COL[CORRECTOR] if entry[4] == "correction" else DIM
            self.label("log" + str(k), "t" + str(entry[0]) + "  #" + str(entry[1]) + " -> #" + str(entry[2])
                       + ("  (correction)" if entry[4] == "correction" else "  (ignored it)" if entry[4] == "ignored" else ""),
                       x0, y, col, 10)
            y += 14
        y += 10

        if self.selected is not None:
            for k, line in enumerate(describe(self.agents, self.selected, self.p)):
                if y > SIM - 66:                              # no room left above the key hints
                    break
                self.label("sel" + str(k), ("Selected " if k == 0 else "") + line, x0, y, WHITE, 10)
                y += 14
        else:
            self.label("sel0", "gold path = chain to the newest person (F)", x0, y, DIM, 10)
            self.label("sel1", "click an agent to trace theirs", x0, y + 14, DIM, 10)

        flags = ("T arrows: " + ("keep" if self.treeMode else "fade") + "   G hop colours: " + ("on" if self.genMode else "off")
                 + "   F follow: " + ("on" if self.follow else "off") + "   H rings: " + ("on" if self.rings else "off"))
        self.label("help0", "S spreader size: " + ("on" if self.spreadMode else "off") + "    ENTER skips the intro", x0, SIM - 54, DIM, 10)
        self.label("help1", "SPACE pause  UP/DOWN speed  R replay  ESC quit", x0, SIM - 38, DIM, 10)
        self.label("help2", flags, x0, SIM - 22, DIM, 10)


def runViewer(build, steps, p, rumour):
    # build() gives a fresh list of agents (used at the start and when R is pressed)
    window = RumourWindow(build, steps, p, rumour)
    arcade.run()
    return window.agents, window.history
