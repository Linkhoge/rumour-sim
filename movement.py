"""Movement for agents, including group visits and avoidance."""
import math
import numpy as np

from agent import NO_GROUP

BOX = 100
GROUP_CENTRES = [(25, 25), (75, 25), (25, 75), (75, 75)]
GROUP_NAMES = ["A", "B", "C", "D"]


def configureGroups(edge):
    """Move the four group centres closer to or further from the edges."""
    if not 0 < edge < 50:
        raise ValueError("group spread must be between 0 and 50")

    GROUP_CENTRES[:] = [
        (edge, edge),
        (100 - edge, edge),
        (edge, 100 - edge),
        (100 - edge, 100 - edge),
    ]


def randomPointNear(centre, radius):
    """Pick a random point inside a circle.

    The square root stops points from gathering near the centre.
    """
    angle = np.random.uniform(0, 2 * math.pi)
    distance = radius * math.sqrt(np.random.random())

    x = centre[0] + distance * math.cos(angle)
    y = centre[1] + distance * math.sin(angle)
    return x, y


def randomPointInBox():
    return tuple(np.random.uniform(0, BOX, 2))


def clampToBox(agent):
    """Keep an agent inside the world."""
    agent.x = min(BOX, max(0, agent.x))
    agent.y = min(BOX, max(0, agent.y))


def randomWalk(agent, step_size):
    """Move an agent by a small random amount."""
    agent.x += step_size * np.random.uniform(-1, 1)
    agent.y += step_size * np.random.uniform(-1, 1)
    clampToBox(agent)


def currentTarget(agent):
    """Return the group an agent is trying to reach."""
    if agent.visiting is not None:
        return agent.visiting

    return agent.group


def moveAgent(agent, step_size, travel_chance, travel_speed, leash, stay_length):
    """Move one agent, either around its group or towards a visited group."""
    can_travel = (
        agent.group != NO_GROUP
        and agent.visiting is None
        and np.random.random() < travel_chance
    )

    if can_travel:
        other_groups = [group for group in range(4) if group != agent.group]
        agent.visiting = int(np.random.choice(other_groups))
        agent.stay = stay_length

    target = currentTarget(agent)

    if target == NO_GROUP:
        randomWalk(agent, step_size)
        return

    centre = GROUP_CENTRES[target]
    dx = centre[0] - agent.x
    dy = centre[1] - agent.y
    distance = math.hypot(dx, dy)

    if distance > leash:
        # Move back towards the group centre.
        speed = min(distance, travel_speed)
        agent.x += speed * dx / distance
        agent.y += speed * dy / distance
    else:
        randomWalk(agent, step_size)

        # Do not let the agent wander outside its group circle.
        dx = agent.x - centre[0]
        dy = agent.y - centre[1]
        distance = math.hypot(dx, dy)

        if distance > leash:
            agent.x = centre[0] + dx * leash / distance
            agent.y = centre[1] + dy * leash / distance

        if agent.visiting is not None:
            agent.stay -= 1

            if agent.stay <= 0:
                agent.visiting = None

    clampToBox(agent)


def segmentDistance(start, end, centre):
    """Find the shortest distance from a centre to a movement path."""
    vx = end[0] - start[0]
    vy = end[1] - start[1]
    length_squared = vx * vx + vy * vy

    if length_squared == 0:
        return math.hypot(start[0] - centre[0], start[1] - centre[1])

    # Find the closest point on the line segment to the centre.
    t = ((centre[0] - start[0]) * vx + (centre[1] - start[1]) * vy) / length_squared
    t = max(0, min(1, t))

    closest_x = start[0] + t * vx
    closest_y = start[1] + t * vy

    return math.hypot(closest_x - centre[0], closest_y - centre[1])


def safeMove(start, desired, centre, radius, side=1):
    """Move an agent without letting its path cross the subject."""
    if radius <= 0:
        return desired

    # Keep the destination inside the world.
    desired_x = min(BOX, max(0, desired[0]))
    desired_y = min(BOX, max(0, desired[1]))
    desired = (desired_x, desired_y)

    safe_radius = radius + 1e-6
    dx = start[0] - centre[0]
    dy = start[1] - centre[1]
    distance = math.hypot(dx, dy)

    # If the agent is already too close, put it just outside the radius.
    if distance < safe_radius:
        if distance == 0:
            angle = 0
        else:
            angle = math.atan2(dy, dx)

        escape_x = centre[0] + safe_radius * math.cos(angle)
        escape_y = centre[1] + safe_radius * math.sin(angle)
        escape = (escape_x, escape_y)

        if 0 <= escape_x <= BOX and 0 <= escape_y <= BOX:
            return escape

        # The direct escape point is outside the world, so try around the circle.
        for angle_step in range(72):
            angle = angle_step * math.pi / 36
            x = centre[0] + safe_radius * math.cos(angle)
            y = centre[1] + safe_radius * math.sin(angle)

            if 0 <= x <= BOX and 0 <= y <= BOX:
                return (x, y)

        raise ValueError("No feasible avoidance point")

    # Accept the normal move if it does not cross the subject.
    if segmentDistance(start, desired, centre) >= radius:
        return desired

    # Otherwise, try moving sideways around the subject.
    normal_x = dx / distance
    normal_y = dy / distance
    move_length = min(2, math.dist(start, desired))

    directions = [
        (-side * normal_y, side * normal_x),
        (side * normal_y, -side * normal_x),
        (normal_x, normal_y),
    ]

    for direction_x, direction_y in directions:
        x = start[0] + move_length * direction_x
        y = start[1] + move_length * direction_y
        candidate = (min(BOX, max(0, x)), min(BOX, max(0, y)))

        if segmentDistance(start, candidate, centre) >= radius:
            return candidate

    # If none of the safe directions work, stay where they are.
    return start


def moveAgents(
    agents,
    step_size,
    travel_chance,
    travel_speed,
    leash,
    stay_length,
    subject=None,
    avoidRadius=0,
    avoidVisualBuffer=1.15,
):
    """Move every agent, then apply friendship and avoidance rules."""
    if subject is not None:
        moveAgent(
            subject,
            step_size,
            travel_chance,
            travel_speed,
            leash,
            stay_length,
        )

    if subject is None:
        centre = None
    else:
        centre = (subject.x, subject.y)

    for agent in agents:
        if agent is subject:
            continue

        start = (agent.x, agent.y)
        moveAgent(
            agent,
            step_size,
            travel_chance,
            travel_speed,
            leash,
            stay_length,
        )

        if centre is None:
            continue

        dx = agent.x - centre[0]
        dy = agent.y - centre[1]
        distance = math.hypot(dx, dy)

        # Keep lingering friends reasonably close to the subject.
        linger_distance = max(1, avoidRadius * 0.8)

        if agent.isFriend and agent.linger and distance > linger_distance:
            agent.x = centre[0] + dx * linger_distance / distance
            agent.y = centre[1] + dy * linger_distance / distance

        if not agent.avoiding or avoidRadius <= 0:
            continue

        # Avoidance is based on where the agent started this step.
        dx = start[0] - centre[0]
        dy = start[1] - centre[1]
        distance = math.hypot(dx, dy)

        outer_radius = avoidRadius * avoidVisualBuffer
        desired = (agent.x, agent.y)
        target = currentTarget(agent)

        # If the subject is blocking the group centre, move around it.
        if target != NO_GROUP:
            group_centre = GROUP_CENTRES[target]

            if math.dist(group_centre, centre) < outer_radius + step_size:
                if distance == 0:
                    angle = agent.routeSide * math.pi / 2
                else:
                    angle = math.atan2(dy, dx)

                agent.avoidAngle = angle

                goal_x = centre[0] + (outer_radius + step_size) * math.cos(angle)
                goal_y = centre[1] + (outer_radius + step_size) * math.sin(angle)
                goal = (goal_x, goal_y)

                vx = goal_x - start[0]
                vy = goal_y - start[1]
                goal_distance = math.hypot(vx, vy)

                if goal_distance > 1e-9:
                    speed = min(goal_distance, travel_speed)
                    desired = (
                        start[0] + speed * vx / goal_distance,
                        start[1] + speed * vy / goal_distance,
                    )

        # Push agents gently away if they are in the soft avoidance zone.
        if avoidRadius < distance < outer_radius:
            pressure = step_size * (outer_radius - distance)
            pressure /= max(outer_radius - avoidRadius, 1e-9)

            desired = (
                desired[0] + pressure * dx / distance,
                desired[1] + pressure * dy / distance,
            )

        agent.x, agent.y = safeMove(
            start,
            desired,
            centre,
            avoidRadius,
            agent.routeSide,
        )

    return agents
