"""Team Char Siu: experimental serial rumour simulation.
Distance-matrix contagion adapted from Le Nguyen (README ref 1).
Order: notice -> subject moves -> others move -> timers -> snapshot spread -> seeds.
Global NumPy RNG and dense distance matrix remain; this is not parallel-ready.
"""
import numpy as np
from scipy.spatial import distance_matrix
from agent import Agent, UNAWARE, SPREADER, CORRECTOR, STIFLER, NO_GROUP
from movement import GROUP_CENTRES, randomPointNear, randomPointInBox, moveAgents


def makeAgents(n, seed, noGroupFraction, leash):
    if n <= 0 or not 0 <= noGroupFraction <= 1:
        raise ValueError('Invalid population or no-group fraction')
    np.random.seed(seed)
    agents = []
    for i in range(n):
        group = NO_GROUP if np.random.random() < noGroupFraction else i % 4
        x, y = randomPointInBox() if group == NO_GROUP else randomPointNear(GROUP_CENTRES[group], leash)
        a = Agent(x, y, UNAWARE, np.random.random(), group, interest=np.random.random())
        a.openness, a.loyalty = np.random.uniform(0, 1, 2)
        a.routeSide = 1 if i % 2 else -1
        agents.append(a)
    return agents


def seedSpreaders(agents, howMany, group):
    options = [i for i, a in enumerate(agents) if a.group == group and not a.isSubject]
    if howMany < 0 or howMany > len(options):
        raise ValueError('Not enough initial spreader candidates')
    for i in np.random.choice(options, howMany, replace=False):
        agents[i].becomeSpreader()
    return agents


def pickSubject(agents, group, friendCount=12, lingerCount=4, friendRadius=4):
    options = [i for i, a in enumerate(agents) if a.group == group and a.state == UNAWARE]
    if not options:
        raise ValueError('No subject candidate in requested group')
    subject = agents[int(np.random.choice(options))]
    subject.isSubject = True
    candidates = [a for a in agents if a is not subject]
    for j, k in enumerate(np.random.choice(len(candidates), min(friendCount, len(candidates)), replace=False)):
        a = candidates[k]
        a.isFriend = a.wasFriend = True
        a.linger = j < lingerCount
        if a.linger:
            a.x, a.y = randomPointNear((subject.x, subject.y), friendRadius)
        if a.believed:
            a.beliefDecided = a.avoiding = False
            a.acceptBelief(-1)
    return agents


def seedCorrectors(agents, howMany, t):
    options = [i for i, a in enumerate(agents) if a.state == UNAWARE and not a.isSubject]
    for i in np.random.choice(options, min(howMany, len(options)), replace=False):
        agents[i].becomeCorrector(-1, 0, t)
    return agents


def getPosition(agents):
    return np.array([[a.x, a.y] for a in agents])


def getState(agents):
    return [a.state for a in agents]


def pickSource(row, old, wanted):
    options = np.where(row & (old == wanted))[0]
    return int(np.random.choice(options)) if len(options) else -1


def rollSpread(agents, t, contactRadius, rumourStrength, correctionStrength, minInterest=1., subjectDenies=1.):
    positions = getPosition(agents)
    close = distance_matrix(positions, positions) < contactRadius
    np.fill_diagonal(close, False)
    old = np.array(getState(agents))
    gen = [a.generation for a in agents]
    corrGen = [a.corrGeneration for a in agents]
    nr = close[:, old == SPREADER].sum(axis=1)
    nc = close[:, old == CORRECTOR].sum(axis=1)
    events = []
    for i, a in enumerate(agents):
        pr = 1 - (1 - a.gullibility * rumourStrength) ** nr[i]
        pc = 1 - (1 - a.openness * correctionStrength) ** nc[i]
        if old[i] == UNAWARE:
            rumour = np.random.random() < pr
            correction = np.random.random() < pc
            if rumour and correction:
                if np.random.random() < 0.5:
                    rumour = False
                else:
                    correction = False
            if rumour:
                s = pickSource(close[i], old, SPREADER)
                if a.isSubject:
                    kind = 'subject' if np.random.random() < subjectDenies else 'ignore'
                elif np.random.random() < minInterest + (1-minInterest)*a.sharingTendency:
                    kind = 'spread'
                else:
                    kind = 'silent'
                events.append((i, kind, s, gen[s]+1))
            elif correction:
                s = pickSource(close[i], old, CORRECTOR)
                events.append((i, 'correct', s, corrGen[s]+1))
        elif old[i] in (SPREADER, STIFLER) and np.random.random() < pc:
            s = pickSource(close[i], old, CORRECTOR)
            events.append((i, 'correct', s, corrGen[s]+1))
    methods = {'spread': 'becomeSpreader', 'silent': 'becomeSilentBeliever',
               'ignore': 'becomeIgnorer', 'subject': 'becomeSubjectCorrector', 'correct': 'becomeCorrector'}
    for i, kind, s, generation in events:
        getattr(agents[i], methods[kind])(s, generation, t)
    return agents


def tickAgents(agents):
    for a in agents:
        a.tick()
    return agents


def stepSimulation(agents, t, p):
    subject = next((a for a in agents if a.isSubject), None)
    for a in agents:
        if not a.beliefDecided:
            a.avoidChance = p.get('avoidChance', 0.75)
    radius = p.get('avoidRadius', 7)
    if subject is not None and subject.state == UNAWARE and radius > 0:
        nearby = [a for a in agents if a.avoiding and (a.x-subject.x)**2+(a.y-subject.y)**2 < (radius+2)**2]
        subject.shunned += len(nearby)
        if nearby and subject.shunned >= p.get('noticeAfter', 20):
            # Noticing is not a transmission: don't invent a teller or hop.
            subject.becomeSubjectCorrector(-1, -1, t)
    moveAgents(agents, p['stepSize'], p['travelChance'], p['travelSpeed'], p['leash'], p['stayLength'], subject, radius)
    tickAgents(agents)
    rollSpread(agents, t, p['contactRadius'], p['rumourStrength'], p['correctionStrength'],
               p.get('minInterest', 0.5), p.get('subjectDenies', 1.))
    if t == p['correctionStart']:
        seedCorrectors(agents, p['correctionSeeds'], t)
    return agents


def countStates(agents):
    states = getState(agents)
    return [states.count(s) for s in range(4)]


def countSpreadersByGroup(agents):
    counts = [0] * 5
    for a in agents:
        if a.state == SPREADER:
            counts[a.group+1] += 1
    return counts


def nearSubject(agents, radius):
    subject = next((a for a in agents if a.isSubject), None)
    near = [] if subject is None else [a for a in agents if a is not subject and (a.x-subject.x)**2+(a.y-subject.y)**2 < radius**2]
    return [len(near), sum(a.believed for a in near)]


def transmissionStats(agents):
    ever = [a for a in agents if a.generation >= 0]
    children = {}
    for a in agents:
        if a.infector >= 0:
            children[a.infector] = children.get(a.infector, 0)+1
    best = max(children, key=children.get) if children else -1
    maxGen = max([a.generation for a in ever], default=0)
    subject = next((a for a in agents if a.isSubject), None)
    heard = subject.heardAt if subject else None
    return dict(everHadRumour=len(ever), maxGeneration=maxGen,
        generationSizes=[sum(a.generation == g for a in ever) for g in range(maxGen+1)],
        passedOnToNobody=sum(i not in children for i, a in enumerate(agents) if a.generation >= 0),
        mostPassedOn=children.get(best, 0), biggestSpreader=best, ignoredIt=sum(a.ignored for a in agents),
        believers=sum(a.believed for a in agents), subjectHeardAtStep=heard,
        subjectHops=subject.generation if subject and subject.generation >= 0 else None,
        heardBeforeSubject=sum(a.heardAt is not None and a.heardAt <= heard for a in agents) if heard is not None else None,
        friends=sum(a.isFriend for a in agents), lostFriends=sum(a.wasFriend and not a.isFriend for a in agents),
        silentBelievers=sum(a.believed and a.state == STIFLER for a in agents))


def runSimulation(agents, steps, p):
    counts, groups, near = [], [], []
    for t in range(steps):
        stepSimulation(agents, t, p)
        counts.append(countStates(agents))
        groups.append(countSpreadersByGroup(agents))
        near.append(nearSubject(agents, p.get('nearRadius', 10)))
    return np.array(counts), np.array(groups), np.array(near)
