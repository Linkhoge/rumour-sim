"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

ARTICLE: marks things taken from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1.
Comments without a tag are ours.

File: agent.py
"""

UNAWARE = 0     # ARTICLE: healthy
SPREADER = 1    # ARTICLE: infected
CORRECTOR = 2   # passes on the correction (README refs 6, 7)
STIFLER = 3     # ARTICLE: recovered. name from Daley-Kendall (README ref 2)

HOW_LONG = 50   # ARTICLE: infectedCounter was 50
NO_GROUP = -1   # agent has no group


class Agent():
    # ARTICLE: Agent has x, y, infected, resistance, infectedCounter
    def __init__(self, x, y, state, gullibility, group, counter=0, interest=1.0):
        self.x = x
        self.y = y
        self.state = state                # ARTICLE: infected
        self.gullibility = gullibility    # ARTICLE: resistance (flipped, see simulation.py)
        self.counter = counter            # ARTICLE: infectedCounter
        self.group = group                # home group (0-3) or NO_GROUP
        self.visiting = None              # group they're visiting right now, None = at home
        self.stay = 0                     # steps left of the visit
        # who told who, -1 = nobody
        self.infector = -1                # who gave them the rumour
        self.generation = -1              # hops from patient zero, -1 = never had it
        self.corrSource = -1              # who gave them the correction
        self.corrGeneration = -1          # hops from the first corrector
        self.changedAt = -2               # step the state last changed (the viewer uses this to draw arrows)
        self.interest = interest          # 0 = doesn't care about gossip, 1 = loves it
        self.isSubject = False            # the rumour is about this agent
        self.ignored = False              # heard it but didn't pass it on
        self.heardAt = None               # step they first heard it, None = never

    def becomeSpreader(self, source=-1, generation=0, t=-1):
        # ARTICLE: infect() sets infected and the counter. we also remember who told us
        self.state = SPREADER
        self.counter = HOW_LONG
        self.infector = source
        self.generation = generation
        self.changedAt = t
        if self.heardAt is None:
            self.heardAt = t

    def becomeIgnorer(self, source, generation, t):
        # heard it but doesn't believe it or doesn't care. goes straight to stifler
        # but still counts as having heard it, and we still record who told them
        self.state = STIFLER
        self.counter = 0
        self.infector = source
        self.generation = generation
        self.ignored = True
        self.changedAt = t
        if self.heardAt is None:
            self.heardAt = t

    def becomeSubjectCorrector(self, source, generation, t):
        # the subject hears the rumour about themselves and denies it. they are the first corrector (hop 0)
        self.state = CORRECTOR
        self.counter = HOW_LONG
        self.infector = source
        self.generation = generation
        self.corrSource = -1
        self.corrGeneration = 0
        self.changedAt = t
        if self.heardAt is None:
            self.heardAt = t

    def becomeCorrector(self, source=-1, generation=0, t=-1):
        # same for the correction, kept separate so the rumour tree stays clean
        self.state = CORRECTOR
        self.counter = HOW_LONG
        self.corrSource = source
        self.corrGeneration = generation
        self.changedAt = t

    def tick(self):
        # ARTICLE: counter counts down, recovers at 0. same for correctors
        if self.state == SPREADER or self.state == CORRECTOR:
            self.counter -= 1
            if self.counter <= 0:
                self.state = STIFLER
