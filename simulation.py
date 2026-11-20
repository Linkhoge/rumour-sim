"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

Comment tags:
    ARTICLE:  from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1
    OUR OWN:  added or changed by us. README reference numbers given where an idea is from research.

File: simulation.py
Setting up agents, spreading rule, one simulation step, main loop. Movement is in movement.py.
"""
import numpy as np
from scipy.spatial import distance_matrix      # ARTICLE: same distance matrix function
from agent import Agent, UNAWARE, SPREADER, CORRECTOR, STIFLER, NO_GROUP
from movement import GROUP_CENTRES, randomPointNear, randomPointInBox, moveAgents


def makeAgents(n, seed, noGroupFraction, leash):
    # ARTICLE: loop that makes agents with random x, y.
    # OUR OWN: most agents belong to a group (shared out evenly) and start near its meeting point.
    # Some agents belong to no group and start anywhere in the box.
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
    # ARTICLE: seed a few infected agents. OUR OWN: all from ONE group so we can watch it reach the others.
    # With howMany = 1 this is "patient zero".
    inGroup = [i for i in range(len(agents)) if agents[i].group == group]
    for i in np.random.choice(inGroup, howMany, replace=False):
        agents[i].becomeSpreader()
    return agents


def pickSubject(agents, group):
    # OUR OWN: the rumour is ABOUT one agent (the subject). They are an ordinary member of a group (choose a
    # different group to patient zero) and are not patient zero. They are not told, they find out like anyone else.
    options = [i for i in range(len(agents)) if agents[i].group == group and agents[i].state == UNAWARE]
    i = int(np.random.choice(options))
    agents[i].isSubject = True
    return agents


def seedCorrectors(agents, howMany, t):
    # OUR OWN: a few unaware agents start spreading the correction
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
    # OUR OWN: if several nearby agents could have passed it on, pick one of them at random
    options = np.where(closeRow & (old == wanted))[0]
    if len(options) == 0:
        return -1
    return int(np.random.choice(options))


def rollSpread(agents, t, contactRadius, rumourStrength, correctionStrength, minInterest=1.0, subjectDenies=1.0):
    # ARTICLE: rollInfect. Distance matrix, then agents within a set distance can pass it on,
    #   with a random roll against resistance (infected if roll > resistance).
    # OUR OWN: roll < gullibility (same idea flipped), two competing messages, and decisions use the
    #   OLD states then get applied at the end, so the order of agents does not matter
    #   (the article changes agents while looping, which depends on the order).
    #   We also record WHO passed it on, so we can draw who told who.
    # OUR OWN: hearing it is not the same as passing it on. Someone who hears the rumour passes it on with chance
    #   minInterest + (1 - minInterest) * their interest. Otherwise they do not believe it or do not care: they become
    #   a stifler at once and stay in the simulation. The subject, when they hear it, denies it (becomes a corrector).
    positions = getPosition(agents)
    dist = distance_matrix(positions, positions)
    close = dist < contactRadius
    np.fill_diagonal(close, False)                 # an agent is not in contact with itself

    old = np.array(getState(agents))
    oldGen = [a.generation for a in agents]        # copies, so applying changes cannot affect each other
    oldCorrGen = [a.corrGeneration for a in agents]
    nr = close[:, old == SPREADER].sum(axis=1)     # spreaders each agent is in contact with
    nc = close[:, old == CORRECTOR].sum(axis=1)    # correctors each agent is in contact with

    newStates = list(old)
    rumourFrom = [-1] * len(agents)
    correctFrom = [-1] * len(agents)
    how = ["correct"] * len(agents)               # OUR OWN: why the state changed (spread, ignore, subject, correct)
    for i in range(len(agents)):
        g = agents[i].gullibility
        pRumour = 1 - (1 - g * rumourStrength) ** nr[i]                    # more contacts, more chances
        pCorrect = 1 - (1 - (1 - g) * correctionStrength) ** nc[i]         # less gullible = more likely to believe it
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
            if np.random.uniform() < pCorrect:     # OUR OWN: spreader changes their mind (README ref 6)
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
    # ARTICLE: the counter countdown inside movement(). Separate function here.
    for agent in agents:
        agent.tick()
    return agents


def stepSimulation(agents, t, p):
    # ONE time step. The viewer and the headless run both call this, so they always match.
    agents = moveAgents(agents, p["stepSize"], p["travelChance"], p["travelSpeed"], p["leash"], p["stayLength"])
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
    # OUR OWN: spreaders per home group. Index 0 = no group, then groups A, B, C, D.
    counts = [0] * (len(GROUP_CENTRES) + 1)
    for a in agents:
        if a.state == SPREADER:
            counts[a.group + 1] += 1
    return counts


def transmissionStats(agents):
    # OUR OWN: numbers about who told who, for the report
    ever = [i for i in range(len(agents)) if agents[i].generation >= 0]
    children = {}
    for a in agents:
        if a.infector >= 0:
            children[a.infector] = children.get(a.infector, 0) + 1
    best = max(children, key=children.get) if children else -1
    maxGen = max([agents[i].generation for i in ever]) if ever else 0
    sizes = [0] * (maxGen + 1)                       # how many agents were in each hop from patient zero
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
        "ignoredIt": len([a for a in agents if a.ignored]),       # heard it, did not pass it on
        "subjectHeardAtStep": subjectHeardAt,                     # None = the subject never found out
        "subjectHops": subjectHops,                               # hops from patient zero to the subject
        "heardBeforeSubject": heardBeforeSubject,                 # how many had heard it when the subject did
    }


def runSimulation(agents, steps, p):
    # ARTICLE: final loop (move, roll infect, record infected count). No drawing, used for headless runs.
    counts = []
    groupCounts = []
    for t in range(steps):
        agents = stepSimulation(agents, t, p)
        counts.append(countStates(agents))
        groupCounts.append(countSpreadersByGroup(agents))
    return np.array(counts), np.array(groupCounts)
