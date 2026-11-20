"""
Team Char Siu
Members: Ariel Fajimiyo (more names to be added)
Module: Agent-based simulation project (serial + parallel)

Comment tags:
    ARTICLE:  from "Simulation 102: Agent-Based Disease Modeling" (Le Nguyen, 2023), README ref 1
    Comments without a tag are ours. README reference numbers are given where an idea is from research.

File: movement.py
All movement logic lives here. Everyone shares one box (no walls). Each group hangs around a meeting
point, agents with no group wander freely, and group members sometimes visit another group then go home.
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
    # ARTICLE: boundary check (set the agent on the boundary if it goes past it)
    agent.x = min(max(agent.x, 0), BOX)
    agent.y = min(max(agent.y, 0), BOX)


def randomWalk(agent, stepSize):
    # ARTICLE: movement(): step of stepSize * uniform(-1, 1) in x and y
    agent.x += stepSize * np.random.uniform(-1, 1)
    agent.y += stepSize * np.random.uniform(-1, 1)
    clampToBox(agent)


def currentTarget(agent):
    # the group the agent is hanging around (the one it is visiting, otherwise its home group)
    if agent.visiting is not None:
        return agent.visiting
    return agent.group


def moveAgent(agent, stepSize, travelChance, travelSpeed, leash, stayLength):
    # start a visit to another group now and then
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
        # too far from the group's meeting point (travelling there): walk straight towards it
        agent.x += travelSpeed * dx / dist
        agent.y += travelSpeed * dy / dist
    else:
        randomWalk(agent, stepSize)
        dx, dy = cx - agent.x, cy - agent.y
        dist = np.sqrt(dx * dx + dy * dy)
        if dist > leash:                         # random step went outside the group area, pull back to the edge
            agent.x = cx - dx * leash / dist
            agent.y = cy - dy * leash / dist
        if agent.visiting is not None:           # arrived and visiting: count down, then go home
            agent.stay -= 1
            if agent.stay <= 0:
                agent.visiting = None


def moveAgents(agents, stepSize, travelChance, travelSpeed, leash, stayLength):
    # ARTICLE: moveAgents (loop over all agents and move each one)
    for agent in agents:
        moveAgent(agent, stepSize, travelChance, travelSpeed, leash, stayLength)
    return agents
