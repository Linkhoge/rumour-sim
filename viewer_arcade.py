"""Original Team Char Siu Arcade viewer, restored from b4e128e.
Distance-model attribution: Le Nguyen, Simulation 102 (README ref 1).
Targeted additions: chart height/hover and clearer unaware/inactive colours.
"""
import math
import numpy as np
import arcade
from agent import UNAWARE, SPREADER, CORRECTOR, STIFLER, NO_GROUP
from movement import BOX, GROUP_CENTRES, GROUP_NAMES
from simulation import stepSimulation, countStates, transmissionStats, nearSubject
SIM = 700
SIDE = 440
SCALE = SIM / BOX
TICKS_PER_SECOND = 30
SMOOTH_RATE = 14
ARROW_LIFE = 5.0
PULSE_LIFE = 1.0
FONT = ('Consolas', 'Menlo', 'DejaVu Sans Mono', 'Courier New')
INTRO_HOLD = 3.0
INTRO_GLIDE = 2.0
INTRO_GAP = 5
GLOW_RADIUS = 11
GLOW_ALPHA = 120
DOT_ACTIVE = 5
DOT_IDLE = 2.5
DOT_HOP = 4
PULSE_SIZE = 18
SPREAD_BASE = 3
SPREAD_GROW = 3
SPREAD_MAX = 16
CHART_HEIGHT = 220
BG = (11,16,32)
PANEL = (17,24,46)
TEXT = (210,218,235)
DIM = (120,130,155)
GOLD = (255,214,10)
WHITE = (255,255,255)
IGNORED_COL = (150,160,185)
SUBJECT_COL = (255,105,180)
SPREAD_COL = (255,159,10)
EX_FRIEND_COL = (167,139,250)
STATE_COL = [(210,220,235),(255,77,77),(46,214,170),(108,118,138)]
LINE_COL = [(210,220,235),(255,77,77),(46,214,170),(145,155,175)]
STATE_NAMES = ['Unaware','Spreader','Corrector','Stifler']
STATE_HELP = ["hasn't heard it",'telling others','spreading the correction','heard it, stopped passing it on']
GROUP_COL = [(244,162,97),(67,97,238),(157,78,221),(141,110,99)]
GEN_COL = [(255,214,10),(255,159,10),(255,99,71),(236,72,153),(168,85,247),(99,102,241),(56,189,248),(45,212,191)]
SPEEDS = [.25,.5,1,2,4,8]

def rgba(col,alpha):
    return (col[0],col[1],col[2],alpha)

def wrap(text,width):
    words = text.split()
    lines,line = [],''
    for w in words:
        if len(line)+len(w)+1 > width:
            lines.append(line)
            line = w
        else:
            line = (line+' '+w).strip()
    lines.append(line)
    return lines

def drawArrow(p1,p2,col,width):
    arcade.draw_line(p1[0],p1[1],p2[0],p2[1],col,width)
    ang = math.atan2(p2[1]-p1[1],p2[0]-p1[0])
    size = 9
    lx,ly = p2[0]-size*math.cos(ang-.45),p2[1]-size*math.sin(ang-.45)
    rx,ry = p2[0]-size*math.cos(ang+.45),p2[1]-size*math.sin(ang+.45)
    arcade.draw_triangle_filled(p2[0],p2[1],lx,ly,rx,ry,col)

def traceChain(agents,idx):
    chain,seen = [],set()
    while 0 <= idx < len(agents) and idx not in seen:
        seen.add(idx)
        chain.append(idx)
        idx = agents[idx].infector
    return chain[::-1]

def nodeColour(a,told=0):
    if a.isFriend or a.isSubject:
        return SUBJECT_COL
    if a.wasFriend:
        return EX_FRIEND_COL
    return SPREAD_COL if a.state == STIFLER and told else STATE_COL[a.state]

def describe(agents,i,p):
    a = agents[i]
    grp = 'no group' if a.group == NO_GROUP else 'group '+GROUP_NAMES[a.group]
    lines = ['#'+str(i)+'  '+STATE_NAMES[a.state]+', '+grp]
    if a.isSubject:
        lines.append('the rumour is about this agent')
    if a.isFriend:
        lines.append('friend of subject'+('; lingers nearby' if a.linger else ''))
    elif a.wasFriend:
        lines.append('former friend; ended at step '+str(a.friendshipEndedAt))
    if a.generation >= 0:
        lines.append('hop '+str(a.generation)+(', started it' if a.infector < 0 else ', told by #'+str(a.infector)))
        if a.ignored:
            lines.append('explicitly rejected the rumour')
    elif a.isSubject and a.heardAt is not None:
        lines.append('noticed avoidance; no direct rumour teller')
    else:
        lines.append('has not had the rumour')
    if a.believed:
        lines.append('believes it; '+('avoids subject' if a.avoiding else 'does not avoid'))
    if a.corrGeneration >= 0:
        lines.append('started correction' if a.corrSource < 0 else 'correction from #'+str(a.corrSource))
    lines.append('gullibility %.2f; openness %.2f' % (a.gullibility,a.openness))
    lines.append('loyalty %.2f; sharing tendency %.2f' % (a.loyalty,a.sharingTendency))
    chance = p.get('minInterest',.5)+(1-p.get('minInterest',.5))*a.sharingTendency
    lines.append('chance to share if accepted: %d%%' % round(100*chance))
    return lines

class RumourWindow(arcade.Window):
    def __init__(self,build,steps,p,rumour):
        super().__init__(SIM+SIDE,SIM,'Team Char Siu - Rumour Spread',vsync=True,antialiasing=True)
        self.background_color = BG
        self.build,self.steps,self.p,self.rumour = build,steps,p,rumour
        self.texts = {}
        self.speedIdx = 1
        self.paused = False
        self.treeMode = False
        self.genMode = False
        self.spreadMode = True
        self.follow = True
        self.rings = False
        self.mousePos = (-1000,-1000)
        self.now = 0.
        self.newRun()
    def newRun(self):
        self.agents = self.build()
        n = len(self.agents)
        self.zeros = [i for i in range(n) if self.agents[i].state == SPREADER]
        self.shown = self.realPositions()
        self.history,self.arrows,self.pulses,self.log = [],[],[],[]
        self.latest = -1
        self.told = [0]*n
        self.top = []
        self.near = nearSubject(self.agents,self.p.get('nearRadius',10))
        self.near0 = self.near[0]
        self.t,self.acc,self.selected,self.intro = 0,0.,None,0.
        mid = BOX/2
        self.introPos = {}
        for j,i in enumerate(self.zeros):
            self.introPos[i] = (mid-INTRO_GAP-2*j,mid)
        for i in range(n):
            if self.agents[i].isSubject:
                self.introPos[i] = (mid+INTRO_GAP,mid)
        for i,pos in self.introPos.items():
            self.shown[i] = pos
        self.glowList,self.dotList = arcade.SpriteList(),arcade.SpriteList()
        self.glows,self.dots = [],[]
        self.dotStyle,self.glowStyle = [None]*n,[None]*n
        for a in self.agents:
            g = arcade.SpriteCircle(GLOW_RADIUS,(255,255,255,255),soft=True)
            g.color = (255,255,255,0)
            self.glowList.append(g)
            self.glows.append(g)
            if a.group == NO_GROUP:
                dot = arcade.SpriteSolidColor(10,10,color=(255,255,255,255))
                dot.angle = 45
            else:
                dot = arcade.SpriteCircle(8,(255,255,255,255))
            self.dotList.append(dot)
            self.dots.append(dot)
    def realPositions(self):
        return np.array([[a.x,a.y] for a in self.agents],dtype=float)
    def toScreen(self,pos):
        return pos[0]*SCALE,pos[1]*SCALE
    def nearestAgent(self,mouse,maxDist):
        best,bestDist = None,maxDist
        for i in range(len(self.agents)):
            sx,sy = self.toScreen(self.shown[i])
            dd = math.hypot(sx-mouse[0],sy-mouse[1])
            if dd < bestDist:
                best,bestDist = i,dd
        return best
    def on_key_press(self,symbol,modifiers):
        k = arcade.key
        if symbol in (k.ESCAPE,k.Q):
            self.close()
        elif symbol == k.SPACE:
            self.paused = not self.paused
        elif symbol == k.ENTER:
            self.intro = INTRO_HOLD+INTRO_GLIDE
        elif symbol == k.UP:
            self.speedIdx = min(self.speedIdx+1,len(SPEEDS)-1)
        elif symbol == k.DOWN:
            self.speedIdx = max(self.speedIdx-1,0)
        elif symbol == k.T:
            self.treeMode = not self.treeMode
        elif symbol == k.G:
            self.genMode = not self.genMode
        elif symbol == k.S:
            self.spreadMode = not self.spreadMode
        elif symbol == k.F:
            self.follow = not self.follow
        elif symbol == k.H:
            self.rings = not self.rings
        elif symbol == k.R:
            self.newRun()
    def on_mouse_motion(self,x,y,dx,dy):
        self.mousePos = (x,y)
    def on_mouse_press(self,x,y,button,modifiers):
        if x < SIM:
            self.selected = self.nearestAgent((x,y),16)
    def on_update(self,delta_time):
        dt = min(delta_time,.05)
        self.now += dt
        introTotal = INTRO_HOLD+INTRO_GLIDE
        intro = self.intro < introTotal
        if intro:
            self.intro += dt
        events = []
        finished = self.t >= self.steps
        if not self.paused and not finished and not intro:
            self.acc += dt*TICKS_PER_SECOND*SPEEDS[self.speedIdx]
            while self.acc >= 1 and self.t < self.steps:
                self.acc -= 1
                stepSimulation(self.agents,self.t,self.p)
                for i in range(len(self.agents)):
                    a = self.agents[i]
                    if a.changedAt == self.t:
                        if a.heardAt == self.t and a.infector >= 0:
                            kind = 'ignored' if a.ignored else 'rumour'
                            col = IGNORED_COL if a.ignored else STATE_COL[SPREADER]
                            events.append((a.infector,i,col,kind,a.generation,self.t))
                            if not a.ignored:
                                self.latest = i
                        elif a.state == CORRECTOR and a.corrSource >= 0:
                            events.append((a.corrSource,i,STATE_COL[CORRECTOR],'correction',a.corrGeneration,self.t))
                self.history.append(countStates(self.agents))
                self.t += 1
        told = [0]*len(self.agents)
        for a in self.agents:
            if a.infector >= 0:
                told[a.infector] += 1
        self.told = told
        order = sorted(range(len(told)),key=lambda i:-told[i])
        self.top = [i for i in order[:5] if told[i] > 0]
        self.near = nearSubject(self.agents,self.p.get('nearRadius',10))
        k = 1-math.exp(-dt*SMOOTH_RATE)
        real = self.realPositions()
        self.shown += (real-self.shown)*k
        if self.intro < introTotal:
            u = max(0.,(self.intro-INTRO_HOLD)/INTRO_GLIDE)
            e = u*u*(3-2*u)
            for i,(ix,iy) in self.introPos.items():
                self.shown[i] = (ix+(real[i][0]-ix)*e,iy+(real[i][1]-iy)*e)
        for src,i,col,kind,hop,tt in events:
            x1,y1 = self.toScreen(self.shown[src])
            x2,y2 = self.toScreen(self.shown[i])
            self.arrows.append([x1,y1,x2,y2,self.now,col])
            self.pulses.append([i,self.now,col])
            self.log.append((tt,src,i,hop,kind))
        if not self.treeMode:
            self.arrows = [h for h in self.arrows if self.now-h[4] < ARROW_LIFE]
        self.pulses = [q for q in self.pulses if self.now-q[1] < PULSE_LIFE]
        self.log = self.log[-60:]
        for i in range(len(self.agents)):
            a = self.agents[i]
            sx,sy = self.toScreen(self.shown[i])
            active = a.state in (SPREADER,CORRECTOR)
            if self.genMode and a.generation >= 0:
                col,rad = GEN_COL[a.generation%len(GEN_COL)],DOT_HOP
            else:
                col,rad = STATE_COL[a.state],DOT_ACTIVE if active else DOT_IDLE
            if self.spreadMode and self.told[i] > 0:
                rad = max(rad,min(SPREAD_MAX,SPREAD_BASE+SPREAD_GROW*math.sqrt(self.told[i])))
                if not active and not self.genMode:
                    col = SPREAD_COL
            dot = self.dots[i]
            dot.position = (sx,sy)
            if self.dotStyle[i] != (col,rad):
                self.dotStyle[i] = (col,rad)
                dot.color = rgba(col,255)
                dot.scale = rad*1.5/10 if a.group == NO_GROUP else rad/8
            glow = self.glows[i]
            glow.position = (sx,sy)
            if active:
                glow.color = rgba(STATE_COL[a.state],GLOW_ALPHA)
                glow.scale = .85+.15*math.sin(self.now*6+i)
                self.glowStyle[i] = True
            elif self.glowStyle[i]:
                glow.color = (255,255,255,0)
                self.glowStyle[i] = False
    def label(self,key,msg,x,ytop,col=TEXT,size=11,bold=False):
        y = SIM-ytop
        t = self.texts.get(key)
        if t is None:
            t = arcade.Text(msg,x,y,col,size,font_name=FONT,bold=bold,anchor_y='top')
            self.texts[key] = t
        else:
            if t.text != msg:
                t.text = msg
            t.position = (x,y)
            if tuple(t.color) != tuple(rgba(col,255)):
                t.color = rgba(col,255)
        t.draw()
    def on_draw(self):
        self.clear()
        p = self.p
        rad = p['leash']*SCALE
        for k in range(len(GROUP_CENTRES)):
            cx,cy = GROUP_CENTRES[k][0]*SCALE,GROUP_CENTRES[k][1]*SCALE
            arcade.draw_circle_filled(cx,cy,rad,rgba(GROUP_COL[k],20))
            arcade.draw_circle_outline(cx,cy,rad,rgba(GROUP_COL[k],90),1)
        self.glowList.draw(blend_function=self.ctx.BLEND_PREMULTIPLIED_ALPHA)
        for h in self.arrows:
            age = self.now-h[4]
            alpha = max(90 if self.treeMode else 0,int(255*(1-age/ARROW_LIFE)))
            drawArrow((h[0],h[1]),(h[2],h[3]),rgba(h[5],alpha),3)
        for q in self.pulses:
            age = self.now-q[1]
            x,y = self.toScreen(self.shown[q[0]])
            arcade.draw_circle_outline(x,y,5+PULSE_SIZE*age/PULSE_LIFE,rgba(q[2],int(255*(1-age/PULSE_LIFE))),2)
        self.dotList.draw()
        if self.rings:
            for i in range(len(self.agents)):
                if self.agents[i].group != NO_GROUP:
                    x,y = self.toScreen(self.shown[i])
                    arcade.draw_circle_outline(x,y,self.dotStyle[i][1]+2 if self.dotStyle[i] else 5,GROUP_COL[self.agents[i].group],1)
        target = self.selected if self.selected is not None else self.latest if self.follow else -1
        if target >= 0:
            chain = traceChain(self.agents,target)
            col = WHITE if self.selected is not None else GOLD
            pts = [self.toScreen(self.shown[j]) for j in chain]
            for k in range(len(pts)-1):
                drawArrow(pts[k],pts[k+1],col,3)
            for k in range(len(pts)):
                arcade.draw_circle_outline(pts[k][0],pts[k][1],9,col,2)
                if self.agents[chain[k]].generation >= 0:
                    self.label('hop'+str(k),str(self.agents[chain[k]].generation),pts[k][0]+8,SIM-pts[k][1]-4,col,10)
        for n,z in enumerate(self.zeros):
            x,y = self.toScreen(self.shown[z])
            arcade.draw_circle_outline(x,y,12+3*math.sin(self.now*4.5),WHITE,2)
            self.label('p0_'+str(n),'PATIENT 0' if len(self.zeros) == 1 else 'P0',x-4,SIM-y-18,WHITE,10,True)
        for i in range(len(self.agents)):
            if self.agents[i].isSubject:
                x,y = self.toScreen(self.shown[i])
                arcade.draw_circle_outline(x,y,14,SUBJECT_COL,2)
                if p.get('avoidRadius',0) > 0:
                    arcade.draw_circle_outline(x,y,p['avoidRadius']*SCALE,rgba(SUBJECT_COL,70),1)
                self.label('subject','SUBJECT',x-4,SIM-y-20,SUBJECT_COL,10,True)
        if self.intro < INTRO_HOLD:
            cx,cy = BOX/2*SCALE,BOX/2*SCALE
            self.label('intro0','PATIENT 0 starts the rumour',cx-110,SIM-cy+30,WHITE,11,True)
            self.label('intro1',"the SUBJECT is who it's about",cx-110,SIM-cy+48,SUBJECT_COL,11,True)
            self.label('intro2','press ENTER to skip',cx-110,SIM-cy+68,DIM,10)
        if self.spreadMode:
            for r,i in enumerate(self.top[:3]):
                x,y = self.toScreen(self.shown[i])
                if r == 0:
                    arcade.draw_circle_outline(x,y,SPREAD_MAX+4,GOLD,2)
                self.label('top'+str(r),'#'+str(i)+' told '+str(self.told[i]),x+12,SIM-y-4,GOLD if r == 0 else TEXT,10,r == 0)
        for k in range(len(GROUP_CENTRES)):
            cx,cy = GROUP_CENTRES[k][0]*SCALE,GROUP_CENTRES[k][1]*SCALE
            self.label('grp'+str(k),'Group '+GROUP_NAMES[k],cx-28,SIM-(cy+rad+4),GROUP_COL[k],10)
        self.drawTooltip()
        self.drawPanel()
    def drawTooltip(self):
        mx,my = self.mousePos
        if mx >= SIM or mx < 0:
            return
        hv = self.nearestAgent(self.mousePos,12)
        if hv is None:
            return
        lines = describe(self.agents,hv,self.p)
        w,h = max(len(s) for s in lines)*7+14,16*len(lines)+8
        bx,by = min(mx+14,SIM-w-4),min(my+8,SIM-h-4)
        arcade.draw_lbwh_rectangle_filled(bx,by,w,h,(30,40,75,235))
        arcade.draw_lbwh_rectangle_outline(bx,by,w,h,(130,145,180),1)
        for k,line in enumerate(lines):
            self.label('tip'+str(k),line,bx+7,SIM-(by+h-5-16*k),TEXT,10)
    def drawPanel(self):
        arcade.draw_lbwh_rectangle_filled(SIM,0,SIDE,SIM,PANEL)
        x0,y = SIM+20,38
        self.label('title','Team Char Siu - Rumour Spread',x0,10,TEXT,14,True)
        for k,line in enumerate(wrap('"'+self.rumour+'"',50)[:2]):
            self.label('rumour'+str(k),line,x0,y,GOLD,11)
            y += 17
        y += 4
        self.label('step','step %d / %d   %sx%s%s%s' % (self.t,self.steps,SPEEDS[self.speedIdx],
            '   PAUSED' if self.paused else '', '   FINISHED (R replays)' if self.t >= self.steps else '',
            '   INTRO' if self.intro < INTRO_HOLD+INTRO_GLIDE else ''),x0,y)
        y += 22
        counts,stats = countStates(self.agents),transmissionStats(self.agents)
        for k in range(4):
            arcade.draw_circle_filled(x0+6,SIM-(y+8),5,LINE_COL[k])
            self.label('count'+str(k),STATE_NAMES[k]+': '+str(counts[k])+'  ('+STATE_HELP[k]+')',x0+20,y)
            y += 18
        self.label('stats','had the rumour: %d   ignored it: %d   believers: %d' % (stats['everHadRumour'],stats['ignoredIt'],stats['believers']),x0,y,DIM,10)
        y += 16
        self.label('near','near the subject: %d (was %d), believers: %d' % (self.near[0],self.near0,self.near[1]),x0,y,SUBJECT_COL,10)
        y += 22
        cw,ch = SIDE-40,CHART_HEIGHT
        bottom = SIM-(y+ch)
        self.chartRect = (x0,bottom,cw,ch)
        arcade.draw_lbwh_rectangle_filled(x0,bottom,cw,ch,(24,32,60))
        arcade.draw_lbwh_rectangle_outline(x0,bottom,cw,ch,(60,72,110),1)
        if len(self.history) > 1:
            for k in range(4):
                pts = [(x0+(j+1)/self.steps*cw,bottom+row[k]/len(self.agents)*ch) for j,row in enumerate(self.history)]
                arcade.draw_line_strip(pts,LINE_COL[k],2)
        self.label('chart','counts over time',x0+6,y+4,DIM,10)
        y += ch+10
        self.label('topTitle','top spreaders (told the most people)',x0,y,DIM,10)
        y += 16
        if not self.top:
            self.label('topNone','nobody has passed it on yet',x0,y,DIM,10)
            y += 14
        for k,i in enumerate(self.top[:3]):
            a = self.agents[i]
            grp = 'no group' if a.group == NO_GROUP else 'group '+GROUP_NAMES[a.group]
            self.label('topRow'+str(k),'#%d  told %d   %s' % (i,self.told[i],grp),x0,y,GOLD if k == 0 else TEXT,10)
            y += 14
        y += 10
        self.label('logTitle','latest passes (teller -> new person)',x0,y,DIM,10)
        y += 16
        for k,entry in enumerate(self.log[::-1][:3]):
            col = LINE_COL[SPREADER] if entry[4] == 'rumour' else LINE_COL[CORRECTOR] if entry[4] == 'correction' else DIM
            suffix = '  (correction)' if entry[4] == 'correction' else '  (ignored it)' if entry[4] == 'ignored' else ''
            self.label('log'+str(k),'t%d  #%d -> #%d%s' % (entry[0],entry[1],entry[2],suffix),x0,y,col,10)
            y += 14
        y += 10
        if self.selected is not None:
            for k,line in enumerate(describe(self.agents,self.selected,self.p)):
                if y > SIM-66:
                    break
                self.label('sel'+str(k),('Selected ' if k == 0 else '')+line,x0,y,WHITE,10)
                y += 14
        else:
            self.label('sel0','gold path = chain to the newest person (F)',x0,y,DIM,10)
            self.label('sel1','click an agent to trace theirs',x0,y+14,DIM,10)
        flags = 'T arrows: '+('keep' if self.treeMode else 'fade')+'   G hop colours: '+('on' if self.genMode else 'off')+'   F follow: '+('on' if self.follow else 'off')+'   H rings: '+('on' if self.rings else 'off')
        self.label('help0','S spreader size: '+('on' if self.spreadMode else 'off')+'    ENTER skips the intro',x0,SIM-54,DIM,10)
        self.label('help1','SPACE pause  UP/DOWN speed  R replay  ESC quit',x0,SIM-38,DIM,10)
        self.label('help2',flags,x0,SIM-22,DIM,10)
        self.drawChartHover()
    def drawChartHover(self):
        x,y,w,h = self.chartRect
        mx,my = self.mousePos
        if not self.history or not (x <= mx <= x+w and y <= my <= y+h):
            return
        step = max(1,min(len(self.history),round((mx-x)/w*self.steps)))
        gx = x+step/self.steps*w
        arcade.draw_line(gx,y,gx,y+h,rgba(TEXT,100),1)
        lines = ['step '+str(step)]+[STATE_NAMES[k]+': '+str(self.history[step-1][k]) for k in range(4)]
        bx,by = min(x+w-170,max(x,mx+10)),min(y+h-4,max(y+90,my+45))
        arcade.draw_lbwh_rectangle_filled(bx,by-90,170,90,(30,40,75,245))
        for k,line in enumerate(lines):
            self.label('chartTip'+str(k),line,bx+6,SIM-(by-5-16*k),TEXT if k == 0 else LINE_COL[k-1],10)

def runViewer(build,steps,p,rumour):
    window = RumourWindow(build,steps,p,rumour)
    arcade.run()
    return window.agents,window.history
