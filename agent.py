"""Agent states and experimental social traits; original timer model adapted from Le Nguyen."""
import numpy as np
UNAWARE, SPREADER, CORRECTOR, STIFLER = range(4)
HOW_LONG = 50
NO_GROUP = -1
class Agent:
    def __init__(self,x,y,state,gullibility,group,counter=0,interest=1.):
        self.x,self.y,self.state = x,y,state
        self.gullibility,self.group,self.counter = gullibility,group,counter
        self.interest = self.sharingTendency = interest
        self.openness = self.loyalty = .5
        self.visiting,self.stay = None,0
        self.infector = self.generation = self.corrSource = self.corrGeneration = -1
        self.changedAt = -2
        self.isSubject = self.ignored = self.believed = False
        self.heardAt = None
        self.shunned = 0
        self.isFriend = self.wasFriend = self.linger = False
        self.friendshipEndedAt = None
        self.avoiding = self.beliefDecided = False
        self.avoidChance,self.routeSide = .75,1
        self.correctionDuration = 110
    def acceptBelief(self,t):
        if self.beliefDecided:
            return
        self.beliefDecided = self.believed = True
        if self.isFriend:
            if np.random.random() >= self.loyalty:
                self.isFriend = self.linger = False
                self.friendshipEndedAt,self.avoiding = t,True
        else:
            self.avoiding = np.random.random() < self.avoidChance
    def becomeSpreader(self,source=-1,generation=0,t=-1):
        self.state,self.counter = SPREADER,HOW_LONG
        self.infector,self.generation,self.changedAt = source,generation,t
        self.acceptBelief(t)
        if self.heardAt is None:
            self.heardAt = t
    def becomeSilentBeliever(self,source,generation,t):
        self.becomeSpreader(source,generation,t)
        self.state,self.counter = STIFLER,0
    def becomeIgnorer(self,source,generation,t):
        self.state,self.counter = STIFLER,0
        self.infector,self.generation,self.changedAt = source,generation,t
        self.ignored,self.believed,self.avoiding = True,False,False
        if self.heardAt is None:
            self.heardAt = t
    def becomeSubjectCorrector(self,source,generation,t):
        self.infector,self.generation = source,generation
        if self.heardAt is None:
            self.heardAt = t
        self.becomeCorrector(-1,0,t)
    def becomeCorrector(self,source=-1,generation=0,t=-1):
        self.state,self.counter = CORRECTOR,self.correctionDuration
        self.corrSource,self.corrGeneration,self.changedAt = source,generation,t
        self.believed = self.avoiding = False
    def tick(self):
        if self.state in (SPREADER,CORRECTOR):
            self.counter -= 1
            if self.counter <= 0:
                self.state = STIFLER
