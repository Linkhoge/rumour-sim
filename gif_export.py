"""CPU-only GIF export. Uses the serial model once; never imports Arcade."""
import argparse
import json
from pathlib import Path
import time
import numpy as np

STATE_NAMES = ('Unaware','Spreader','Corrector','Stifler')
STATE_COL = ('#d2dceb','#ff4d4d','#2ed6aa','#6c768a')
GROUP_COL = ('#f4a261','#4361ee','#9d4edd','#8d6e63')


def positiveInt(value):
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError('must be positive')
    return n


def snapshot(agents,step):
    states = np.array([a.state for a in agents],dtype=np.int8)
    sources = np.array([a.infector for a in agents],dtype=int)
    return dict(step=step,positions=np.array([(a.x,a.y) for a in agents]),states=states,
        groups=np.array([a.group for a in agents]),friend=np.array([a.isFriend for a in agents]),
        former=np.array([a.wasFriend and not a.isFriend for a in agents]),
        avoiding=np.array([a.avoiding for a in agents]),believed=np.array([a.believed for a in agents]),
        subject=np.array([a.isSubject for a in agents]),
        corrected=sum(a.corrGeneration >= 0 for a in agents),
        told=np.bincount(sources[sources >= 0],minlength=len(agents)))


def recordRun(agents,steps,p,every=4):
    from simulation import stepSimulation,countStates,countSpreadersByGroup,nearSubject
    from movement import GROUP_CENTRES
    if not agents or steps <= 0 or every <= 0:
        raise ValueError('population, steps and frame interval must be positive')
    frames = [snapshot(agents,0)]
    counts = [countStates(agents)]
    near = [nearSubject(agents,p.get('nearRadius',10))]
    groups = [countSpreadersByGroup(agents)]
    zeros = [i for i,a in enumerate(agents) if a.state == 1]
    for t in range(steps):
        stepSimulation(agents,t,p)
        counts.append(countStates(agents))
        near.append(nearSubject(agents,p.get('nearRadius',10)))
        groups.append(countSpreadersByGroup(agents))
        if (t+1)%every == 0 or t+1 == steps:
            frames.append(snapshot(agents,t+1))
    return dict(frames=frames,counts=np.array(counts),near=np.array(near),groups=np.array(groups),
        zeros=zeros,centres=list(GROUP_CENTRES),settings=dict(p),steps=steps,n=len(agents),every=every)


def saveGif(run,path,rumour,fps=15,width=1000,seed=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation,PillowWriter
    from matplotlib.patches import Circle
    from matplotlib.path import Path as MarkerPath
    if fps <= 0 or width < 480:
        raise ValueError('fps must be positive; width must be at least 480 pixels')
    path = Path(path)
    if path.suffix.lower() != '.gif':
        raise ValueError('output must use the .gif extension')
    path.parent.mkdir(parents=True,exist_ok=True)
    fig = plt.figure(figsize=(width/100,width*.65/100),dpi=100,facecolor='#0b1020')
    grid = fig.add_gridspec(3,2,width_ratios=(1.2,1),height_ratios=(1,1,.9))
    world = fig.add_subplot(grid[:,0])
    curve = fig.add_subplot(grid[0,1])
    proximity = fig.add_subplot(grid[1,1])
    info = fig.add_subplot(grid[2,1])
    diamond = MarkerPath([(0,1.5),(.75,0),(0,-1.5),(-.75,0),(0,1.5)],
                         [MarkerPath.MOVETO,MarkerPath.LINETO,MarkerPath.LINETO,MarkerPath.LINETO,MarkerPath.CLOSEPOLY])
    fig.suptitle(rumour[:100],color='#d2daeb',fontsize=10)
    fig.subplots_adjust(left=.055,right=.98,bottom=.08,top=.91,wspace=.28,hspace=.65)
    p = run['settings']

    def style(ax,title):
        ax.clear()
        ax.set_facecolor('#11182e')
        ax.set_title(title,color='#d2daeb',fontsize=9)
        ax.tick_params(colors='#aab5cc',labelsize=7)
        for spine in ax.spines.values():
            spine.set_color('#46506e')

    def draw(index):
        frame = run['frames'][index]
        step = frame['step']
        positions = frame['positions']
        states = frame['states']
        active = np.isin(states,[1,2])
        radius = np.where(active,5.75,3.25)
        shared = frame['told'] > 0
        radius[shared] = np.maximum(radius[shared],np.minimum(16,3+3*np.sqrt(frame['told'][shared])))
        colours = [('#ff69b4' if frame['subject'][i] or frame['friend'][i] else
                    '#a78bfa' if frame['former'][i] else '#ff9f0a' if states[i] == 3 and shared[i] else STATE_COL[states[i]])
                   for i in range(run['n'])]
        style(world,'Agent positions - step %d / %d' % (step,run['steps']))
        world.set(xlim=(0,100),ylim=(0,100),aspect='equal')
        for i,centre in enumerate(run['centres']):
            world.add_patch(Circle(centre,p['leash'],facecolor=GROUP_COL[i],edgecolor=GROUP_COL[i],alpha=.12))
            world.text(centre[0],centre[1]+p['leash']+1,'ABCD'[i],color=GROUP_COL[i],ha='center',fontsize=8)
        for noGroup,marker in [(False,'o'),(True,diamond)]:
            mask = (frame['groups'] == -1) == noGroup
            if mask.any():
                world.scatter(positions[mask,0],positions[mask,1],s=(2*radius[mask])**2,
                              c=np.array(colours)[mask],marker=marker,linewidths=.4,zorder=3)
        avoids = frame['avoiding'] & ~frame['subject']
        if avoids.any():
            world.scatter(positions[avoids,0],positions[avoids,1],s=(2*(radius[avoids]+4.5))**2,
                          facecolors='none',edgecolors='#ff5f5f',linewidths=.7,zorder=4)
        relation = (frame['friend'] | frame['former']) & active
        if relation.any():
            world.scatter(positions[relation,0],positions[relation,1],s=(2*(radius[relation]+2))**2,
                          facecolors='none',edgecolors=np.array(STATE_COL)[states[relation]],linewidths=.7,zorder=4)
        for i in np.flatnonzero(frame['subject']):
            world.add_patch(Circle(positions[i],p.get('avoidRadius',7),fill=False,edgecolor='#ff69b4',alpha=.5))
            world.annotate('SUBJECT',positions[i],xytext=(5,8),textcoords='offset points',color='#ff69b4',fontsize=7)
        for i in run['zeros']:
            world.annotate('P0',positions[i],xytext=(5,-9),textcoords='offset points',color='white',fontsize=7)
        x = np.arange(step+1)
        style(curve,'State counts')
        for k,name in enumerate(STATE_NAMES):
            curve.plot(x,run['counts'][:step+1,k],color=STATE_COL[k],label=name,lw=1.2)
        curve.set(xlim=(0,run['steps']),ylim=(0,run['n']))
        curve.axvline(step,color='white',alpha=.25,lw=.6)
        curve.legend(fontsize=6,ncol=2,facecolor='#11182e',labelcolor='#d2daeb',loc='upper right')
        style(proximity,'Within %g units of subject' % p.get('nearRadius',10))
        proximity.plot(x,run['near'][:step+1,0],color='#ff69b4',label='All')
        proximity.plot(x,run['near'][:step+1,1],color='#ff4d4d',label='Believers')
        proximity.set(xlim=(0,run['steps']),ylim=(0,max(1,int(run['near'].max()))))
        proximity.legend(fontsize=6,facecolor='#11182e',labelcolor='#d2daeb',loc='upper right')
        style(info,'Run statistics')
        info.axis('off')
        leaders = sorted(range(run['n']),key=lambda i:(-frame['told'][i],i))[:3]
        top = ', '.join('#%d: %d' % (i,frame['told'][i]) for i in leaders if frame['told'][i]) or 'none'
        text = 'Believers: %d   Avoiding: %d\nFriends: %d   Lost: %d   Ever corrected: %d\nDirect recipients: %s\nCircle: home group   Diamond: no group\nRed outer ring: avoiding subject' % (
            frame['believed'].sum(),avoids.sum(),frame['friend'].sum(),frame['former'].sum(),frame['corrected'],top)
        info.text(0,1,text,transform=info.transAxes,va='top',color='#d2daeb',fontsize=7,linespacing=1.6)

    animation = FuncAnimation(fig,draw,frames=len(run['frames']),interval=1000/fps,repeat=False,cache_frame_data=False)
    try:
        animation.save(str(path),writer=PillowWriter(fps=fps),dpi=100)
    finally:
        plt.close(fig)
    metadata = dict(seed=seed,n=run['n'],steps=run['steps'],settings=p,fps=fps,width=width,
                    every=run['every'],frame_steps=[f['step'] for f in run['frames']],rumour=rumour)
    path.with_suffix('.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    return path


def main(argv=None):
    from main import parseArgs,settingsFromArgs,buildAgents
    parser = argparse.ArgumentParser(description='Export agents, state curves and statistics as a GIF.',
        epilog='Other arguments are passed to main.py; use python main.py --help for model settings.')
    parser.add_argument('--output',default='results/simulation.gif')
    parser.add_argument('--fps',type=positiveInt,default=15)
    parser.add_argument('--every',type=positiveInt,default=4)
    parser.add_argument('--width',type=positiveInt,default=1000)
    exportArgs,modelArgs = parser.parse_known_args(argv)
    if exportArgs.width < 480 or Path(exportArgs.output).suffix.lower() != '.gif':
        parser.error('width must be at least 480; output must end in .gif')
    args = parseArgs(modelArgs)
    p = settingsFromArgs(args)
    try:
        agents = buildAgents(args.n,args.seed,p)
    except ValueError as exc:
        parser.error(str(exc))
    rumour = args.rumour or 'The canteen is closing next week'
    start = time.perf_counter()
    run = recordRun(agents,args.steps,p,exportArgs.every)
    recorded = time.perf_counter()-start
    start = time.perf_counter()
    path = saveGif(run,exportArgs.output,rumour,exportArgs.fps,exportArgs.width,args.seed)
    print('GIF:',path,'frames:',len(run['frames']))
    print('model + recording seconds:',recorded,'render + encode seconds:',time.perf_counter()-start)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
