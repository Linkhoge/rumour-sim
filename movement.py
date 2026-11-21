"""Team Char Siu: shared-space group movement and circular avoidance.
Random walk/bounds adapted from Le Nguyen (README ref 1). Routing is experimental.
"""
import math
import numpy as np
from agent import NO_GROUP

BOX = 100
GROUP_CENTRES = [(33, 33), (67, 33), (33, 67), (67, 67)]
GROUP_NAMES = ['A', 'B', 'C', 'D']


def randomPointNear(centre, radius):
    angle = np.random.uniform(0, 2 * math.pi)
    r = radius * math.sqrt(np.random.random())
    return centre[0] + r * math.cos(angle), centre[1] + r * math.sin(angle)


def randomPointInBox():
    return tuple(np.random.uniform(0, BOX, 2))


def clampToBox(a):
    a.x, a.y = min(BOX, max(0, a.x)), min(BOX, max(0, a.y))


def randomWalk(a, stepSize):
    a.x += stepSize * np.random.uniform(-1, 1)
    a.y += stepSize * np.random.uniform(-1, 1)
    clampToBox(a)


def currentTarget(a):
    return a.visiting if a.visiting is not None else a.group


def moveAgent(a, stepSize, travelChance, travelSpeed, leash, stayLength):
    if a.group != NO_GROUP and a.visiting is None and np.random.random() < travelChance:
        a.visiting = int(np.random.choice([g for g in range(4) if g != a.group]))
        a.stay = stayLength
    target = currentTarget(a)
    if target == NO_GROUP:
        randomWalk(a, stepSize)
        return
    cx, cy = GROUP_CENTRES[target]
    dx, dy = cx - a.x, cy - a.y
    d = math.hypot(dx, dy)
    if d > leash:
        travel = min(d, travelSpeed)
        a.x += travel * dx / d
        a.y += travel * dy / d
    else:
        randomWalk(a, stepSize)
        dx, dy = a.x - cx, a.y - cy
        d = math.hypot(dx, dy)
        if d > leash:
            a.x, a.y = cx + dx * leash / d, cy + dy * leash / d
        if a.visiting is not None:
            a.stay -= 1
            if a.stay <= 0:
                a.visiting = None
    clampToBox(a)


def segmentDistance(p, q, c):
    vx, vy = q[0] - p[0], q[1] - p[1]
    length2 = vx * vx + vy * vy
    t = max(0, min(1, ((c[0]-p[0])*vx + (c[1]-p[1])*vy)/length2)) if length2 else 0
    return math.hypot(p[0] + t*vx - c[0], p[1] + t*vy - c[1])


def safeMove(start, desired, centre, radius, side=1):
    """Reject disk-crossing segments; detour tangentially. Evacuate initial overlaps.
    Evacuation is a positional correction, not speed-limited physical movement.
    """
    px, py = start
    cx, cy = centre
    q = (min(BOX, max(0, desired[0])), min(BOX, max(0, desired[1])))
    if radius <= 0:
        return q
    r = radius + 1e-6
    d = math.hypot(px-cx, py-cy)
    if d < r:
        angle = math.atan2(py-cy, px-cx) if d else 0
        candidates = [(cx+r*math.cos(angle), cy+r*math.sin(angle))]
        candidates += [(cx+r*math.cos(t*math.pi/36), cy+r*math.sin(t*math.pi/36)) for t in range(72)]
        valid = [p for p in candidates if 0 <= p[0] <= BOX and 0 <= p[1] <= BOX]
        if not valid:
            raise ValueError('Avoidance radius has no feasible boundary point')
        return min(valid, key=lambda p: math.dist(p, start))
    if segmentDistance(start, q, centre) >= radius:
        return q
    nx, ny = (px-cx)/d, (py-cy)/d
    length = min(2., math.dist(start, q))
    for dx, dy in ((-side*ny, side*nx), (side*ny, -side*nx), (nx, ny)):
        candidate = (min(BOX, max(0, px+length*dx)), min(BOX, max(0, py+length*dy)))
        if segmentDistance(start, candidate, centre) >= radius:
            return candidate
    return start


def moveAgents(agents, stepSize, travelChance, travelSpeed, leash, stayLength,
               subject=None, avoidRadius=0, avoidSpeed=0, avoidChance=0):
    # Subject-first scheduling gives all other agents one common centre this step.
    if subject is not None:
        moveAgent(subject, stepSize, travelChance, travelSpeed, leash, stayLength)
    centre = (subject.x, subject.y) if subject is not None else None
    for a in agents:
        if a is subject:
            continue
        start = (a.x, a.y)
        moveAgent(a, stepSize, travelChance, travelSpeed, leash, stayLength)
        if centre is not None and a.isFriend and a.linger:
            # Nearby friends wander around the subject instead of following a group leash.
            cx, cy = centre
            dx, dy = a.x-cx, a.y-cy
            d = math.hypot(dx, dy)
            limit = max(1., avoidRadius * 0.8)
            if d > limit:
                a.x, a.y = cx + dx*limit/d, cy + dy*limit/d
        if centre is not None and a.avoiding:
            a.x, a.y = safeMove(start, (a.x, a.y), centre, avoidRadius, a.routeSide)
    return agents
