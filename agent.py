"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

Comment tags:
    ARTICLE:  from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1
    Comments without a tag are ours. README reference numbers are given where an idea is from research.

File: agent.py
"""

UNAWARE = 0     # ARTICLE: healthy
SPREADER = 1    # ARTICLE: infected
CORRECTOR = 2   # passes on the correction (README refs 6, 7)
STIFLER = 3     # ARTICLE: recovered. Name from Daley-Kendall (README ref 2)

HOW_LONG = 50   # ARTICLE: infectedCounter was set to 50
NO_GROUP = -1   # agents who do not belong to any group


class Agent():
    # ARTICLE: Agent has x, y, infected, resistance, infectedCounter
    def __init__(self, x, y, state, gullibility, group, counter=0, interest=1.0):
        self.x = x
        self.y = y
        self.state = state                # ARTICLE: infected
        self.gullibility = gullibility    # ARTICLE: resistance (flipped, see simulation.py)
        self.counter = counter            # ARTICLE: infectedCounter
        self.group = group                # home group (0, 1, 2, 3) or NO_GROUP
        self.visiting = None              # group being visited right now (None = at home)
        self.stay = 0                     # steps left of the visit
        # who told who. -1 means nobody (the agent started with it, or never got it).
        self.infector = -1                # agent number who gave this agent the RUMOUR
        self.generation = -1              # hops from patient zero (0 = started with it, -1 = never had it)
        self.corrSource = -1              # agent number who gave this agent the CORRECTION
        self.corrGeneration = -1          # hops from the first corrector
        self.changedAt = -2               # step when the state last changed (used to draw new hops)
        self.interest = interest          # how much they care about gossip (0 = not at all, 1 = loves it)
        self.isSubject = False            # the rumour is ABOUT this agent
        self.ignored = False              # heard the rumour but chose not to pass it on
        self.heardAt = None               # step they first heard the rumour (None = never)

    def becomeSpreader(self, source=-1, generation=0, t=-1):
        # ARTICLE: infect() sets infected and the counter. We also remember who told us.
        self.state = SPREADER
        self.counter = HOW_LONG
        self.infector = source
        self.generation = generation
        self.changedAt = t
        if self.heardAt is None:
            self.heardAt = t

    def becomeIgnorer(self, source, generation, t):
        # Heard the rumour but does not believe it or does not care, so never passes it on.
        # They stay in the simulation as a stifler. We still record who told them (to draw the arrow).
        self.state = STIFLER
        self.counter = 0
        self.infector = source
        self.generation = generation
        self.ignored = True
        self.changedAt = t
        if self.heardAt is None:
            self.heardAt = t

    def becomeSubjectCorrector(self, source, generation, t):
        # The subject hears the rumour about themselves and denies it. They are the FIRST corrector
        # (corrSource -1, hop 0). We still record who told them the rumour (infector, generation).
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
        # same for the correction (kept separate so the rumour tree stays clean)
        self.state = CORRECTOR
        self.counter = HOW_LONG
        self.corrSource = source
        self.corrGeneration = generation
        self.changedAt = t

    def tick(self):
        # ARTICLE: counter ticks down, agent recovers at 0. We do the same for correctors.
        if self.state == SPREADER or self.state == CORRECTOR:
            self.counter -= 1
            if self.counter <= 0:
                self.state = STIFLER
