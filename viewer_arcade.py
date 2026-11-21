"""Live Arcade viewer. Hover chart/agents; click to inspect a transmission chain."""
import math
import arcade
import numpy as np
from agent import SPREADER,CORRECTOR,STIFLER
from movement import GROUP_CENTRES,GROUP_NAMES,safeMove
from simulation import stepSimulation,countStates,transmissionStats,nearSubject
SIM,SIDE,CHART_HEIGHT = 700,440,280
STATE_NAMES = ['Unaware','Spreader','Corrector','Stifler']
STATE_COL = [(225,232,245),(255,77,77),(46,214,170),(110,120,140)]
SUBJECT_COL,EX_FRIEND_COL,ORANGE = (255,105,180),(167,139,250),(255,159,10)
TEXT = (220,228,240)
SPEEDS = [.25,.5,1,2,4,8]

def nodeColour(a,told=0):
    if a.isSubject or a.isFriend:
        return SUBJECT_COL
    if a.wasFriend:
        return EX_FRIEND_COL
    return ORANGE if a.state == STIFLER and told else STATE_COL[a.state]

def traceChain(agents,i):
    chain,seen = [],set()
    while 0 <= i < len(agents) and i not in seen:
        seen.add(i)
        chain.append(i)
        i = agents[i].infector
    return chain[::-1]

def describe(agents,i,p):
    a = agents[i]
    relationship = 'subject' if a.isSubject else 'friend' if a.isFriend else 'ex-friend' if a.wasFriend else 'not a friend'
    return ['#%d %s; %s' % (i,STATE_NAMES[a.state],relationship),
        'believes %s; avoids %s' % (a.believed,a.avoiding),
        'gullibility %.2f; openness %.2f' % (a.gullibility,a.openness),
        'loyalty %.2f; sharing %.2f' % (a.loyalty,a.sharingTendency),
        'rumour from #%d; correction from #%d' % (a.infector,a.corrSource)]

class RumourWindow(arcade.Window):
    def __init__(self,build,steps,p,rumour):
        super().__init__(SIM+SIDE,SIM,'Team Char Siu - Rumour Spread',vsync=True)
        self.background_color = (11,16,32)
        self.build,self.steps,self.p,self.rumour = build,steps,p,rumour
        self.texts,self.mouse = {},(-1,-1)
        self.speed,self.paused,self.links,self.sizes = 1,False,False,True
        self.now = 0.
        self.newRun()
    def newRun(self):
        self.agents = self.build()
        self.shown = np.array([[a.x,a.y] for a in self.agents],dtype=float)
        self.history,self.events = [],[]
        self.t,self.acc,self.intro,self.selected = 0,0.,0.,None
        self.subject = next((i for i,a in enumerate(self.agents) if a.isSubject),None)
        self.zeros = [i for i,a in enumerate(self.agents) if a.state == SPREADER]
        self.introPos = {i:(45-2*j,50) for j,i in enumerate(self.zeros)}
        if self.subject is not None:
            self.introPos[self.subject] = (55,50)
        for i,pos in self.introPos.items():
            self.shown[i] = pos
        self.told = [0]*len(self.agents)
        self.near0 = nearSubject(self.agents,self.p['nearRadius'])[0]
    def label(self,key,text,x,y,col=TEXT,size=10):
        obj = self.texts.get(key)
        if obj is None:
            obj = arcade.Text(text,x,y,col,size,anchor_y='top')
            self.texts[key] = obj
        else:
            obj.text,obj.position,obj.color = text,(x,y),col
        obj.draw()
    def point(self,i):
        return self.shown[i]*7
    def nearest(self,x,y):
        distances = np.linalg.norm(self.shown*7-[x,y],axis=1)
        i = int(np.argmin(distances))
        return i if distances[i] < 14 else None
    def on_mouse_motion(self,x,y,dx,dy):
        self.mouse = (x,y)
    def on_mouse_press(self,x,y,button,modifiers):
        if x < SIM:
            self.selected = self.nearest(x,y)
    def on_key_press(self,key,modifiers):
        k = arcade.key
        if key in (k.ESCAPE,k.Q):
            self.close()
        elif key == k.SPACE:
            self.paused = not self.paused
        elif key == k.ENTER:
            self.intro = 5.
        elif key == k.UP:
            self.speed = min(5,self.speed+1)
        elif key == k.DOWN:
            self.speed = max(0,self.speed-1)
        elif key == k.R:
            self.newRun()
        elif key == k.T:
            self.links = not self.links
        elif key == k.S:
            self.sizes = not self.sizes
    def on_update(self,delta_time):
        dt = min(delta_time,.05)
        self.now += dt
        previous = self.shown.copy()
        if self.intro < 5:
            self.intro += dt
        elif not self.paused:
            self.acc += dt*30*SPEEDS[self.speed]
            while self.acc >= 1 and self.t < self.steps:
                self.acc -= 1
                stepSimulation(self.agents,self.t,self.p)
                for i,a in enumerate(self.agents):
                    source = a.corrSource if a.state == CORRECTOR else a.infector
                    if a.changedAt == self.t and source >= 0:
                        self.events.append((source,i,self.now,a.state))
                self.history.append(countStates(self.agents))
                self.t += 1
        real = np.array([[a.x,a.y] for a in self.agents])
        self.shown += (real-self.shown)*(1-math.exp(-dt*14))
        if self.intro < 5:
            u = max(0,min(1,(self.intro-3)/2))
            u = u*u*(3-2*u)
            for i,pos in self.introPos.items():
                self.shown[i] = np.array(pos)+(real[i]-pos)*u
        elif self.subject is not None:
            for i,a in enumerate(self.agents):
                if a.avoiding:
                    self.shown[i] = safeMove(previous[i],self.shown[i],self.shown[self.subject],self.p['avoidRadius'],a.routeSide)
        self.events = [e for e in self.events if self.now-e[2] < 1.5]
        self.told = [0]*len(self.agents)
        for a in self.agents:
            if a.infector >= 0:
                self.told[a.infector] += 1
    def on_draw(self):
        self.clear()
        for i,c in enumerate(GROUP_CENTRES):
            x,y = c[0]*7,c[1]*7
            arcade.draw_circle_outline(x,y,self.p['leash']*7,(90,100,135,110),1)
            self.label('group'+str(i),'Group '+GROUP_NAMES[i],x-20,y+self.p['leash']*7+15)
        if self.links:
            for source,target,born,state in self.events:
                arcade.draw_line(*self.point(source),*self.point(target),(*STATE_COL[state],int(170*(1-(self.now-born)/1.5))),1)
        if self.selected is not None:
            chain = traceChain(self.agents,self.selected)
            for i,j in zip(chain,chain[1:]):
                arcade.draw_line(*self.point(i),*self.point(j),(220,228,240,150),1)
        for i,a in enumerate(self.agents):
            x,y = self.point(i)
            radius = 4 if a.state in (SPREADER,CORRECTOR) else 2.5
            if self.sizes and self.told[i]:
                radius = max(radius,min(14,3+2*math.sqrt(self.told[i])))
            arcade.draw_circle_filled(x,y,radius,nodeColour(a,self.told[i]))
            if (a.isFriend or a.wasFriend) and a.state in (SPREADER,CORRECTOR):
                arcade.draw_circle_outline(x,y,radius+2,STATE_COL[a.state],1.5)
            if a.isSubject:
                arcade.draw_circle_outline(x,y,12,SUBJECT_COL,2)
                for scale,alpha in [(1,90),(self.p['avoidVisualBuffer'],35)]:
                    arcade.draw_circle_outline(x,y,self.p['avoidRadius']*scale*7,(*SUBJECT_COL,alpha),1)
                self.label('subject','SUBJECT',x+14,y+16,SUBJECT_COL)
            if i in self.zeros:
                arcade.draw_circle_outline(x,y,10,TEXT,1)
                self.label('p0'+str(i),'PATIENT 0',x+12,y+16)
        if self.intro < 5:
            self.label('intro','Patient 0 and subject - ENTER skips intro',15,650)
        self.drawPanel()
        x,y = self.mouse
        i = self.nearest(x,y) if 0 <= x < SIM else None
        if i is not None:
            lines = describe(self.agents,i,self.p)
            bx,by = min(x+10,365),max(100,min(690,y+100))
            arcade.draw_lbwh_rectangle_filled(bx,by-95,330,95,(30,40,65,245))
            for j,line in enumerate(lines):
                self.label('tip'+str(j),line,bx+5,by-5-17*j,size=9)
    def drawPanel(self):
        x = 715
        arcade.draw_lbwh_rectangle_filled(700,0,440,700,(17,24,46))
        self.label('title','Team Char Siu - Rumour Spread',x,685,size=14)
        self.label('rumour',self.rumour[:55],x,660)
        self.label('step','Step %d / %d  %.2gx%s' % (self.t,self.steps,SPEEDS[self.speed],' PAUSED' if self.paused else ''),x,640)
        counts,stats = countStates(self.agents),transmissionStats(self.agents)
        for k in range(4):
            self.label('count'+str(k),'%s: %d' % (STATE_NAMES[k],counts[k]),x,620-16*k,STATE_COL[k])
        near = nearSubject(self.agents,self.p['nearRadius'])
        self.label('near','Near subject %d (start %d); believers %d' % (near[0],self.near0,near[1]),x,550,SUBJECT_COL)
        self.label('social','Friends %d; ex-friends %d; ever corrected %d' % (stats['friends'],stats['lostFriends'],stats['everCorrected']),x,534)
        self.label('silent','Silent believers %d; explicit rejections %d' % (stats['silentBelievers'],stats['ignoredIt']),x,518)
        self.drawChart(x,220,400,280)
        lines = [('Pink: friend / subject; violet: ex-friend',SUBJECT_COL),('Red/green outline = active rumour/correction',TEXT),
            ('Orange: stopped sharing, previously told others',ORANGE),('Pale: unaware; grey: inactive',TEXT),
            ('Click node: trace its rumour chain',TEXT),('T: recent links (off by default); S: influence size',TEXT),
            ('SPACE pause; UP/DOWN speed; R replay; ESC quit',TEXT)]
        for j,(line,col) in enumerate(lines):
            self.label('legend'+str(j),line,x,205-20*j,col,size=9)
    def drawChart(self,x,y,w,h):
        arcade.draw_lbwh_rectangle_filled(x,y,w,h,(24,32,60))
        n = len(self.agents)
        for fraction in (0,.5,1):
            yy = y+fraction*h
            arcade.draw_line(x,yy,x+w,yy,(65,75,100),1)
            self.label('axis'+str(fraction),str(round(n*fraction)),x+3,yy+12,size=8)
        if len(self.history) > 1:
            for k in range(4):
                points = [(x+(j+1)/self.steps*w,y+row[k]/n*h) for j,row in enumerate(self.history)]
                arcade.draw_line_strip(points,STATE_COL[k],2)
        mx,my = self.mouse
        if self.history and x <= mx <= x+w and y <= my <= y+h:
            step = max(1,min(len(self.history),round((mx-x)/w*self.steps)))
            gx = x+step/self.steps*w
            arcade.draw_line(gx,y,gx,y+h,(220,228,240,100),1)
            lines = ['Step '+str(step)]+['%s: %d' % (STATE_NAMES[k],self.history[step-1][k]) for k in range(4)]
            bx,by = min(x+w-155,max(x,mx+10)),min(y+h-4,max(y+88,my+45))
            arcade.draw_lbwh_rectangle_filled(bx,by-88,155,88,(30,40,65,245))
            for k,line in enumerate(lines):
                self.label('ctip'+str(k),line,bx+5,by-4-16*k,TEXT if k == 0 else STATE_COL[k-1],9)

def runViewer(build,steps,p,rumour):
    window = RumourWindow(build,steps,p,rumour)
    arcade.run()
    return window.agents,window.history
