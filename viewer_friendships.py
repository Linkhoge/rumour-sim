"""Friendship overlay on the existing Arcade viewer; original viewer is retained.
Pink centres show friendship, not belief. Red/green outlines show message activity.
"""
import math
import arcade
import viewer_arcade as base
from agent import SPREADER, CORRECTOR, STIFLER, NO_GROUP
from movement import safeMove
from simulation import transmissionStats


def describe(agents, i, p):
    a = agents[i]
    group = 'no group' if a.group == NO_GROUP else 'group ' + base.GROUP_NAMES[a.group]
    lines = ['#%d  %s, %s' % (i, base.STATE_NAMES[a.state], group)]
    if a.isSubject:
        lines.append('the subject of the rumour')
    if a.isFriend:
        lines.append('friend of subject' + ('; lingers nearby' if a.linger else ''))
    elif a.wasFriend:
        lines.append('former friend; ended at step ' + str(a.friendshipEndedAt))
    if a.generation >= 0:
        lines.append('hop %d; told by %s' % (a.generation, '#'+str(a.infector) if a.infector >= 0 else 'nobody (seed)'))
    elif a.isSubject and a.heardAt is not None:
        lines.append('noticed avoidance; no direct rumour teller')
    else:
        lines.append('has not accepted the rumour')
    if a.believed:
        lines.append('believes it; ' + ('avoids subject' if a.avoiding else 'does not avoid'))
        if a.state == STIFLER:
            lines.append('not currently sharing (silent or stopped)')
    if a.corrGeneration >= 0:
        lines.append('started correction' if a.corrSource < 0 else 'correction from #' + str(a.corrSource))
    lines.append('gullibility %.2f; openness %.2f' % (a.gullibility, a.openness))
    lines.append('loyalty %.2f; sharing tendency %.2f' % (a.loyalty, a.sharingTendency))
    chance = p.get('minInterest', 0.5) + (1-p.get('minInterest', 0.5))*a.sharingTendency
    lines.append('chance to share if accepted: %d%%' % round(100*chance))
    return lines


class FriendshipWindow(base.RumourWindow):
    def __init__(self, build, steps, p, rumour):
        # Base layout reads these before creating the window and drawing its chart.
        base.SIDE = 640
        base.CHART_HEIGHT = 180
        super().__init__(build, steps, p, rumour)

    def on_update(self, delta_time):
        previous = self.shown.copy()
        super().on_update(delta_time)
        subject = next((i for i, a in enumerate(self.agents) if a.isSubject), None)
        if subject is not None and self.intro >= base.INTRO_HOLD + base.INTRO_GLIDE:
            centre = self.shown[subject].copy()
            for i, a in enumerate(self.agents):
                if a.avoiding:
                    self.shown[i] = safeMove(previous[i], self.shown[i], centre, self.p.get('avoidRadius', 7), a.routeSide)
                position = self.toScreen(self.shown[i])
                self.dots[i].position = position
                self.glows[i].position = position
        for i, a in enumerate(self.agents):
            if a.isFriend or a.isSubject:
                self.dots[i].color = base.rgba(base.SUBJECT_COL, 255)
                # Invalidate colour cache so a breakup restores ordinary colour next frame.
                self.dotStyle[i] = None

    def drawTooltip(self):
        # Base viewer resolves its describe function through its module globals.
        original = base.describe
        base.describe = describe
        try:
            super().drawTooltip()
        finally:
            base.describe = original

    def drawPanel(self):
        original = base.describe
        base.describe = describe
        try:
            super().drawPanel()
        finally:
            base.describe = original

    def on_draw(self):
        super().on_draw()
        for i, a in enumerate(self.agents):
            if a.isFriend and a.state in (SPREADER, CORRECTOR):
                x, y = self.toScreen(self.shown[i])
                radius = min(base.SPREAD_MAX, max(base.DOT_ACTIVE, base.SPREAD_BASE + base.SPREAD_GROW*math.sqrt(self.told[i]))) if self.told[i] else base.DOT_ACTIVE
                arcade.draw_circle_outline(x, y, radius+2, base.STATE_COL[a.state], 2)
        stats = transmissionStats(self.agents)
        self.label('friendsOverlay', 'Friends: %d   Lost: %d   Silent/stopped believers: %d' %
                   (stats['friends'], stats['lostFriends'], stats['silentBelievers']), 12, 10, base.SUBJECT_COL, 10)


def runViewer(build, steps, p, rumour):
    window = FriendshipWindow(build, steps, p, rumour)
    arcade.run()
    return window.agents, window.history
