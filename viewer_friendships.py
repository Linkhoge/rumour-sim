"""Small friendship overlay; the original Arcade viewer remains the base."""
import math
import arcade
import viewer_arcade as base
from agent import SPREADER,CORRECTOR
from movement import safeMove
from simulation import transmissionStats
from viewer_effects import drawThinArrow,showsAvoidance,AVOID_RING_COL,AVOID_RING_WIDTH,AVOID_RING_GAP
EX_FRIEND_COL = base.EX_FRIEND_COL
class FriendshipWindow(base.RumourWindow):
    def __init__(self,build,steps,p,rumour):
        # Replace only the arrow drawing primitive, keeping T/F and chain logic intact.
        base.drawArrow = drawThinArrow
        super().__init__(build,steps,p,rumour)
    def on_update(self,delta_time):
        previous = self.shown.copy()
        super().on_update(delta_time)
        subject = next((i for i,a in enumerate(self.agents) if a.isSubject),None)
        if subject is not None and self.intro >= base.INTRO_HOLD+base.INTRO_GLIDE:
            centre = self.shown[subject].copy()
            for i,a in enumerate(self.agents):
                if a.avoiding:
                    self.shown[i] = safeMove(previous[i],self.shown[i],centre,self.p.get('avoidRadius',7),a.routeSide)
                self.dots[i].position = self.toScreen(self.shown[i])
                self.glows[i].position = self.dots[i].position
        for i,a in enumerate(self.agents):
            if a.isFriend or a.wasFriend or a.isSubject:
                self.dots[i].color = base.rgba(base.nodeColour(a,self.told[i]),255)
                self.dotStyle[i] = None
    def on_draw(self):
        super().on_draw()
        for i,a in enumerate(self.agents):
            x,y = self.toScreen(self.shown[i])
            active = a.state in (SPREADER,CORRECTOR)
            radius = base.DOT_HOP if self.genMode and a.generation >= 0 else base.DOT_ACTIVE if active else base.DOT_IDLE
            if self.spreadMode and self.told[i]:
                radius = max(radius,min(base.SPREAD_MAX,base.SPREAD_BASE+base.SPREAD_GROW*math.sqrt(self.told[i])))
            if (a.isFriend or a.wasFriend) and active:
                arcade.draw_circle_outline(x,y,radius+2,base.STATE_COL[a.state],2)
            if showsAvoidance(a):
                arcade.draw_circle_outline(x,y,radius+AVOID_RING_GAP,AVOID_RING_COL,AVOID_RING_WIDTH)
        stats = transmissionStats(self.agents)
        self.label('friendsOverlay','Friends: %d   Lost: %d   Silent/stopped believers: %d' %
            (stats['friends'],stats['lostFriends'],stats['silentBelievers']),12,10,base.SUBJECT_COL,10)
        self.label('avoidanceLegend','Red outer ring = avoiding the subject',12,26,AVOID_RING_COL[:3],10)

def runViewer(build,steps,p,rumour):
    window = FriendshipWindow(build,steps,p,rumour)
    arcade.run()
    return window.agents,window.history
