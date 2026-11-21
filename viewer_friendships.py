"""Small friendship overlay; the original Arcade viewer remains the base."""
import math
import arcade
import viewer_arcade as base
from agent import SPREADER,CORRECTOR
from movement import safeMove
from simulation import transmissionStats
EX_FRIEND_COL = base.EX_FRIEND_COL
class FriendshipWindow(base.RumourWindow):
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
            if (a.isFriend or a.wasFriend) and a.state in (SPREADER,CORRECTOR):
                x,y = self.toScreen(self.shown[i])
                radius = base.DOT_ACTIVE
                if self.spreadMode and self.told[i]:
                    radius = max(radius,min(base.SPREAD_MAX,base.SPREAD_BASE+base.SPREAD_GROW*math.sqrt(self.told[i])))
                arcade.draw_circle_outline(x,y,radius+2,base.STATE_COL[a.state],2)
        stats = transmissionStats(self.agents)
        self.label('friendsOverlay','Friends: %d   Lost: %d   Silent/stopped believers: %d' %
            (stats['friends'],stats['lostFriends'],stats['silentBelievers']),12,10,base.SUBJECT_COL,10)

def runViewer(build,steps,p,rumour):
    window = FriendshipWindow(build,steps,p,rumour)
    arcade.run()
    return window.agents,window.history
