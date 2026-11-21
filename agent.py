"""Team Char Siu: agent state and experimental social traits.
Position, timers and contagion structure adapted from Le Nguyen (README ref 1).
Friendship/loyalty and separate correction/sharing decisions are our model rules.
"""
import numpy as np

UNAWARE, SPREADER, CORRECTOR, STIFLER = range(4)
HOW_LONG = 50
NO_GROUP = -1


class Agent:
    def __init__(self, x, y, state, gullibility, group, counter=0, interest=1.0):
        self.x, self.y, self.state = x, y, state
        self.gullibility, self.group, self.counter = gullibility, group, counter
        self.interest = interest
        self.sharingTendency = interest
        self.openness = 0.5
        self.loyalty = 0.5
        self.visiting, self.stay = None, 0
        self.infector = self.generation = self.corrSource = self.corrGeneration = -1
        self.changedAt = -2
        self.isSubject = self.ignored = self.believed = False
        self.heardAt = None
        self.shunned = 0
        self.isFriend = self.wasFriend = self.linger = False
        self.friendshipEndedAt = None
        self.avoiding = False
        self.avoidChance = 0.75
        self.beliefDecided = False
        self.routeSide = 1

    def acceptBelief(self, t):
        # Only one friendship/avoidance decision, not another draw every step.
        if self.beliefDecided:
            return
        self.beliefDecided = True
        self.believed = True
        if self.isFriend:
            if np.random.random() >= self.loyalty:
                self.isFriend = self.linger = False
                self.friendshipEndedAt = t
                self.avoiding = True
        else:
            self.avoiding = np.random.random() < self.avoidChance

    def becomeSpreader(self, source=-1, generation=0, t=-1):
        self.state, self.counter = SPREADER, HOW_LONG
        self.infector, self.generation, self.changedAt = source, generation, t
        self.acceptBelief(t)
        if self.heardAt is None:
            self.heardAt = t

    def becomeSilentBeliever(self, source, generation, t):
        self.becomeSpreader(source, generation, t)
        self.state, self.counter = STIFLER, 0

    def becomeIgnorer(self, source, generation, t):
        self.state, self.counter = STIFLER, 0
        self.infector, self.generation, self.changedAt = source, generation, t
        self.ignored, self.believed, self.avoiding = True, False, False
        if self.heardAt is None:
            self.heardAt = t

    def becomeSubjectCorrector(self, source, generation, t):
        self.infector, self.generation = source, generation
        if self.heardAt is None:
            self.heardAt = t
        self.becomeCorrector(-1, 0, t)

    def becomeCorrector(self, source=-1, generation=0, t=-1):
        # Correctors remain committed for the rest of this run; counter is unused.
        self.state, self.counter = CORRECTOR, 0
        self.corrSource, self.corrGeneration, self.changedAt = source, generation, t
        self.believed = self.avoiding = False
        # Accepting the correction does not automatically repair a friendship.

    def tick(self):
        # Only rumour spreaders lose interest after 50 steps.
        if self.state == SPREADER:
            self.counter -= 1
            if self.counter <= 0:
                self.state = STIFLER
