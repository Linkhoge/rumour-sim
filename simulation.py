"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

ARTICLE: marks things taken from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1.
Comments without a tag are ours.

File: simulation.py
Setting up agents, the spread rule, one step, and the main loop. Movement is in movement.py.
"""
import numpy as np
from scipy.spatial import distance_matrix      # ARTICLE: same distance matrix function
from agent import Agent, UNAWARE, SPREADER, CORRECTOR, STIFLER, NO_GROUP
from movement import GROUP_CENTRES, randomPointNear, randomPointInBox, moveAgents


def makeAgents(n, seed, noGroupFraction, leash):
    # ARTICLE: loop that makes agents with random x, y.
    # most agents get a group (shared out evenly) and start near its meeting point,
    # the rest have no group and start anywhere in the box.
    # the seed is set here so one seed decides the whole run
    np.random.seed(seed)
    agents = []
    for i in range(n):
        if np.random.uniform() < noGroupFraction:
            x, y = randomPointInBox()
            group = NO_GROUP
        else:
            group = i % len(GROUP_CENTRES)
            x, y = randomPointNear(GROUP_CENTRES[group], leash)
        agents.append(Agent(x, y, UNAWARE, np.random.uniform(), group, interest=np.random.uniform()))
    return agents


def seedSpreaders(agents, howMany, group):
    # ARTICLE: seed a few infected agents. ours all come from one group so we can watch it reach the others.
    # howMany = 1 is patient zero
    inGroup = [i for i in range(len(agents)) if agents[i].group == group]
    for i in np.random.choice(inGroup, howMany, replace=False):
        agents[i].becomeSpreader()
    return agents


def pickSubject(agents, group):
    # the rumour is about one agent (the subject). pick a group other than patient zero's.
    # they aren't told first, they find out like everyone else
    options = [i for i in range(len(agents)) if agents[i].group == group and agents[i].state == UNAWARE]
    i = int(np.random.choice(options))
    agents[i].isSubject = True
    return agents


def seedCorrectors(agents, howMany, t):
    # a few unaware agents start spreading the correction
    unaware = [i for i in range(len(agents)) if agents[i].state == UNAWARE]
    if len(unaware) == 0:
        return agents
    for i in np.random.choice(unaware, min(howMany, len(unaware)), replace=False):
        agents[i].becomeCorrector(-1, 0, t)
    return agents


def getPosition(agents):
    # ARTICLE: getPosition
    positions = []
    for agent in agents:
        positions.append([agent.x, agent.y])
    return np.array(positions)


def getState(agents):
    # ARTICLE: getInfected (we return the state number)
    return [agent.state for agent in agents]


def pickSource(closeRow, old, wanted):
    # if a few nearby agents could have told them, pick one at random
    options = np.where(closeRow & (old == wanted))[0]
    if len(options) == 0:
        return -1
    return int(np.random.choice(options))


def rollSpread(agents, t, contactRadius, rumourStrength, correctionStrength, minInterest=1.0, subjectDenies=1.0):
    # ARTICLE: rollInfect. distance matrix, anyone within a set distance can pass it on,
    #   random roll against resistance.
    # what we changed:
    #   - roll < gullibility (same idea flipped), and there are two messages (rumour + correction)
    #   - everyone decides from the OLD states, then the changes are applied at the end, so the
    #     order of agents doesn't matter (the article updates while looping so it does)
    #   - we record who passed it on so we can draw who told who
    #   - hearing it isn't the same as passing it on. if you hear it you pass it on with chance
    #     minInterest + (1 - minInterest) * interest, otherwise you become a stifler straight away
    #   - the subject denies it when they hear it (becomes a corrector)
    positions = getPosition(agents)
    dist = distance_matrix(positions, positions)
    close = dist < contactRadius
    np.fill_diagonal(close, False)                 # agent isn't in contact with itself

    old = np.array(getState(agents))
    oldGen = [a.generation for a in agents]        # copies so applying changes can't affect each other
    oldCorrGen = [a.corrGeneration for a in agents]
    nr = close[:, old == SPREADER].sum(axis=1)     # spreaders each agent is in contact with
    nc = close[:, old == CORRECTOR].sum(axis=1)    # correctors each agent is in contact with

    newStates = list(old)
    rumourFrom = [-1] * len(agents)
    correctFrom = [-1] * len(agents)
    how = ["correct"] * len(agents)               # why the state changed: spread, ignore, subject or correct
    for i in range(len(agents)):
        g = agents[i].gullibility
        pRumour = 1 - (1 - g * rumourStrength) ** nr[i]                    # more contacts, more chances
        pCorrect = 1 - (1 - (1 - g) * correctionStrength) ** nc[i]         # less gullible = more likely to believe the correction
        if old[i] == UNAWARE:
            gotRumour = np.random.uniform() < pRumour
            gotCorrect = np.random.uniform() < pCorrect
            if gotRumour and gotCorrect:           # heard both this step, coin flip
                if np.random.uniform() < 0.5:
                    gotRumour = False
                else:
                    gotCorrect = False
            if gotRumour:
                rumourFrom[i] = pickSource(close[i], old, SPREADER)
                if agents[i].isSubject:
                    if np.random.uniform() < subjectDenies:
                        newStates[i] = CORRECTOR
                        how[i] = "subject"
                    else:
                        newStates[i] = STIFLER
                        how[i] = "ignore"
                elif np.random.uniform() < minInterest + (1 - minInterest) * agents[i].interest:
                    newStates[i] = SPREADER
                    how[i] = "spread"
                else:
                    newStates[i] = STIFLER
                    how[i] = "ignore"
            elif gotCorrect:
                newStates[i] = CORRECTOR
                correctFrom[i] = pickSource(close[i], old, CORRECTOR)
        elif old[i] == SPREADER:
            if np.random.uniform() < pCorrect:     # spreader changes their mind (README ref 6)
                newStates[i] = CORRECTOR
                correctFrom[i] = pickSource(close[i], old, CORRECTOR)

    for i in range(len(agents)):
        if newStates[i] != old[i]:
            if how[i] == "spread":
                s = rumourFrom[i]
                agents[i].becomeSpreader(s, oldGen[s] + 1, t)
            elif how[i] == "ignore":
                s = rumourFrom[i]
                agents[i].becomeIgnorer(s, oldGen[s] + 1, t)
            elif how[i] == "subject":
                s = rumourFrom[i]
                agents[i].becomeSubjectCorrector(s, oldGen[s] + 1, t)
            else:
                s = correctFrom[i]
                agents[i].becomeCorrector(s, oldCorrGen[s] + 1, t)
    return agents


def tickAgents(agents):
    # ARTICLE: the counter countdown from movement(), separate function here
    for agent in agents:
        agent.tick()
    return agents


def stepSimulation(agents, t, p):
    # one time step. the viewer and headless both call this so they always match
    subject = None
    if p.get("avoidRadius", 0) > 0:                # find the subject so believers can keep away from them
        for a in agents:
            if a.isSubject:
                subject = a
                break
    if subject is not None and subject.state == UNAWARE:
        # the subject hasn't heard it, but they notice when believers keep coming close and then keeping away.
        # after enough of that they realise something is going on and deny it (counted from the old positions)
        r2 = p["avoidRadius"] ** 2
        close = [((a.x - subject.x) ** 2 + (a.y - subject.y) ** 2, i) for i, a in enumerate(agents)
                 if a.believed and not a.isSubject and (a.x - subject.x) ** 2 + (a.y - subject.y) ** 2 < r2]
        subject.shunned += len(close)
        if close and subject.shunned >= p.get("noticeAfter", 20):
            s = min(close)[1]                      # the nearest believer is the one they noticed
            subject.becomeSubjectCorrector(s, agents[s].generation + 1, t)
    agents = moveAgents(agents, p["stepSize"], p["travelChance"], p["travelSpeed"], p["leash"], p["stayLength"],
                        subject, p.get("avoidRadius", 0), p.get("avoidSpeed", 0), p.get("avoidChance", 0))
    agents = tickAgents(agents)
    agents = rollSpread(agents, t, p["contactRadius"], p["rumourStrength"], p["correctionStrength"],
                         p.get("minInterest", 1.0), p.get("subjectDenies", 1.0))
    if t == p["correctionStart"]:
        agents = seedCorrectors(agents, p["correctionSeeds"], t)
    return agents


def countStates(agents):
    # [unaware, spreader, corrector, stifler]
    states = getState(agents)
    return [states.count(s) for s in range(4)]


def countSpreadersByGroup(agents):
    # spreaders per home group. index 0 = no group, then A to D
    counts = [0] * (len(GROUP_CENTRES) + 1)
    for a in agents:
        if a.state == SPREADER:
            counts[a.group + 1] += 1
    return counts


def nearSubject(agents, radius):
    # [everyone, believers] within radius of the subject (shows how isolated they are)
    for a in agents:
        if a.isSubject:
            allNear = 0
            believersNear = 0
            for b in agents:
                if b is not a and (b.x - a.x) ** 2 + (b.y - a.y) ** 2 < radius * radius:
                    allNear += 1
                    if b.believed:
                        believersNear += 1
            return [allNear, believersNear]
    return [0, 0]


def transmissionStats(agents):
    # numbers about who told who, for the report
    ever = [i for i in range(len(agents)) if agents[i].generation >= 0]
    children = {}
    for a in agents:
        if a.infector >= 0:
            children[a.infector] = children.get(a.infector, 0) + 1
    best = max(children, key=children.get) if children else -1
    maxGen = max([agents[i].generation for i in ever]) if ever else 0
    sizes = [0] * (maxGen + 1)                       # agents per hop from patient zero
    for i in ever:
        sizes[agents[i].generation] += 1
    subject = [a for a in agents if a.isSubject]
    subjectHeardAt = None
    subjectHops = None
    heardBeforeSubject = None
    if subject and subject[0].heardAt is not None:
        subjectHeardAt = subject[0].heardAt
        subjectHops = subject[0].generation
        heardBeforeSubject = len([a for a in agents if a.heardAt is not None and a.heardAt <= subjectHeardAt])
    return {
        "everHadRumour": len(ever),
        "maxGeneration": maxGen,
        "generationSizes": sizes,
        "passedOnToNobody": len([i for i in ever if i not in children]),
        "mostPassedOn": children[best] if best >= 0 else 0,
        "biggestSpreader": best,
        "ignoredIt": len([a for a in agents if a.ignored]),       # heard it, didn't pass it on
        "believers": len([a for a in agents if a.believed]),      # believe it (and keep away from the subject)
        "subjectHeardAtStep": subjectHeardAt,                     # None = never found out
        "subjectHops": subjectHops,                               # hops from patient zero to the subject
        "heardBeforeSubject": heardBeforeSubject,                 # how many had heard it by then
    }


def runSimulation(agents, steps, p):
    # ARTICLE: final loop (move, roll infect, record counts). no drawing, used for headless runs
    counts = []
    groupCounts = []
    near = []                                      # how many agents are near the subject at each step
    for t in range(steps):
        agents = stepSimulation(agents, t, p)
        counts.append(countStates(agents))
        groupCounts.append(countSpreadersByGroup(agents))
        near.append(nearSubject(agents, p.get("nearRadius", 10)))
    return np.array(counts), np.array(groupCounts), np.array(near)
