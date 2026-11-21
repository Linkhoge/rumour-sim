"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

ARTICLE: marks things taken from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1.
Comments without a tag are ours.

File: movement.py
All the movement is here. Everyone shares one box with no walls. Each group hangs around a meeting
point, agents with no group wander, and group members sometimes visit another group then go home.
Agents who believe the rumour keep away from the subject.
"""
import numpy as np
from agent import NO_GROUP

BOX = 100                                                       # ARTICLE: bounds were [0, 100]
GROUP_CENTRES = [(33, 33), (67, 33), (33, 67), (67, 67)]        # meeting point of each group
GROUP_NAMES = ["A", "B", "C", "D"]


def randomPointNear(centre, radius):
    # random point inside a circle around the centre
    angle = np.random.uniform(0, 2 * np.pi)
    r = radius * np.sqrt(np.random.uniform())
    return centre[0] + r * np.cos(angle), centre[1] + r * np.sin(angle)


def randomPointInBox():
    # ARTICLE: x, y = uniform(0, 100)
    return np.random.uniform(0, BOX), np.random.uniform(0, BOX)


def clampToBox(agent):
    # ARTICLE: boundary check, put the agent on the edge if it goes past
    agent.x = min(max(agent.x, 0), BOX)
    agent.y = min(max(agent.y, 0), BOX)


def randomWalk(agent, stepSize):
    # ARTICLE: movement(): step of stepSize * uniform(-1, 1) in x and y
    agent.x += stepSize * np.random.uniform(-1, 1)
    agent.y += stepSize * np.random.uniform(-1, 1)
    clampToBox(agent)


def currentTarget(agent):
    # the group they're hanging around: the one they're visiting, otherwise home
    if agent.visiting is not None:
        return agent.visiting
    return agent.group


def moveAgent(agent, stepSize, travelChance, travelSpeed, leash, stayLength):
    # now and then start a visit to another group
    if agent.group != NO_GROUP and agent.visiting is None and np.random.uniform() < travelChance:
        others = [g for g in range(len(GROUP_CENTRES)) if g != agent.group]
        agent.visiting = int(np.random.choice(others))
        agent.stay = stayLength

    target = currentTarget(agent)
    if target == NO_GROUP:
        randomWalk(agent, stepSize)             # no group: wander anywhere
        return

    cx, cy = GROUP_CENTRES[target]
    dx, dy = cx - agent.x, cy - agent.y
    dist = np.sqrt(dx * dx + dy * dy)
    if dist > leash:
        # too far from the meeting point (still travelling there): walk straight at it
        agent.x += travelSpeed * dx / dist
        agent.y += travelSpeed * dy / dist
    else:
        randomWalk(agent, stepSize)
        dx, dy = cx - agent.x, cy - agent.y
        dist = np.sqrt(dx * dx + dy * dy)
        if dist > leash:                         # random step took them outside the group area, pull back to the edge
            agent.x = cx - dx * leash / dist
            agent.y = cy - dy * leash / dist
        if agent.visiting is not None:           # arrived and visiting: count down, then go home
            agent.stay -= 1
            if agent.stay <= 0:
                agent.visiting = None


def avoidSubject(agent, subject, avoidRadius, avoidSpeed, avoidChance, stayLength):
    # a believer who gets within avoidRadius of the subject is pushed away from them (most of the time).
    # a believer from the subject's own group leaves to visit another group instead of staying close
    dx, dy = agent.x - subject.x, agent.y - subject.y
    dist = np.sqrt(dx * dx + dy * dy)
    if dist >= avoidRadius or np.random.uniform() >= avoidChance:
        return
    if dist < 0.01:                              # right on top of them, pick any direction
        angle = np.random.uniform(0, 2 * np.pi)
        dx, dy, dist = np.cos(angle), np.sin(angle), 1.0
    agent.x += avoidSpeed * dx / dist
    agent.y += avoidSpeed * dy / dist
    clampToBox(agent)
    if agent.group != NO_GROUP and agent.group == subject.group and agent.visiting is None:
        others = [g for g in range(len(GROUP_CENTRES)) if g != agent.group]
        agent.visiting = int(np.random.choice(others))
        agent.stay = stayLength


def moveAgents(agents, stepSize, travelChance, travelSpeed, leash, stayLength,
               subject=None, avoidRadius=0, avoidSpeed=0, avoidChance=0):
    # ARTICLE: moveAgents (loop over everyone and move them)
    for agent in agents:
        moveAgent(agent, stepSize, travelChance, travelSpeed, leash, stayLength)
        if subject is not None and agent.believed and not agent.isSubject:     # believers keep away from the subject
            avoidSubject(agent, subject, avoidRadius, avoidSpeed, avoidChance, stayLength)
    return agents
