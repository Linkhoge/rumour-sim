"""Import-safe CLI entry point."""
import argparse
import math
import time
from pathlib import Path

def positiveInt(value):
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError('must be positive')
    return n

def makeSettings(n,correctionStrength=.03,groupSpread=33,leash=15,avoidVisualBuffer=1.15,correctionDuration=50,correctionRadius=None):
    if not isinstance(n,int) or isinstance(n,bool) or n <= 0:
        raise ValueError('population must be a positive integer')
    contactRadius = 4*math.sqrt(500/n)
    if correctionRadius is None:
        correctionRadius = contactRadius
    if not all(math.isfinite(v) for v in (correctionStrength,groupSpread,leash,avoidVisualBuffer,correctionDuration,correctionRadius)):
        raise ValueError('settings must be finite')
    if not 0 <= correctionStrength <= 1 or correctionDuration <= 0 or correctionRadius <= 0:
        raise ValueError('invalid correction strength, duration or radius')
    if not 0 < groupSpread < 50 or not 0 < leash <= min(groupSpread,50-groupSpread) or avoidVisualBuffer < 1:
        raise ValueError('invalid spacing, leash or buffer')
    return dict(stepSize=1.5,contactRadius=contactRadius,rumourStrength=.06,
        correctionStrength=correctionStrength,correctionStart=60,correctionSeeds=0,correctionDuration=correctionDuration,correctionRadius=correctionRadius,
        minInterest=.5,subjectDenies=1.,avoidRadius=7,avoidChance=.75,noticeAfter=20,nearRadius=10,
        leash=leash,travelChance=.003,travelSpeed=2.,stayLength=40,groupSpread=groupSpread,avoidVisualBuffer=avoidVisualBuffer)

def parseArgs(argv=None):
    p = argparse.ArgumentParser(description='Team Char Siu rumour simulation')
    p.add_argument('rumour',nargs='?')
    p.add_argument('--n',type=positiveInt,default=500)
    p.add_argument('--steps',type=positiveInt,default=400)
    p.add_argument('--seed',type=int,default=42)
    p.add_argument('--headless',action='store_true')
    for name,default in [('correction-strength',.03),('group-spread',33),('leash',15),('avoid-visual-buffer',1.15),('correction-radius',None)]:
        p.add_argument('--'+name,type=float,default=default)
    p.add_argument('--correction-duration',type=positiveInt,default=50)
    args = p.parse_args(argv)
    if not 0 <= args.seed < 2**32:
        p.error('seed must be between 0 and 4294967295')
    try:
        settingsFromArgs(args)
    except ValueError as exc:
        p.error(str(exc))
    return args

def settingsFromArgs(a):
    return makeSettings(a.n,a.correction_strength,a.group_spread,a.leash,a.avoid_visual_buffer,a.correction_duration,a.correction_radius)

def buildAgents(n,seed,settings):
    from movement import configureGroups
    from simulation import makeAgents,seedSpreaders,pickSubject
    configureGroups(settings['groupSpread'])
    agents = makeAgents(n,seed,.2,settings['leash'])
    for a in agents:
        a.correctionDuration = settings['correctionDuration']
    seedSpreaders(agents,1,0)
    return pickSubject(agents,3,friendCount=12,lingerCount=4,friendRadius=min(4,settings['avoidRadius']*.7))

def main(argv=None):
    args = parseArgs(argv)
    rumour = args.rumour
    if rumour is None:
        rumour = input('Type the rumour: ').strip()
    rumour = rumour or 'The canteen is closing next week'
    p = settingsFromArgs(args)
    def build():
        return buildAgents(args.n,args.seed,p)
    from simulation import runSimulation,transmissionStats
    try:
        agents = build()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.headless:
        from plots import plotCurve,plotGroupSpreaders,plotNearSubject,plotTree
        Path('results').mkdir(exist_ok=True)
        start = time.perf_counter()
        counts,groups,near = runSimulation(agents,args.steps,p)
        stats = transmissionStats(agents)
        plotCurve(counts,'results/curve.png',rumour)
        plotGroupSpreaders(groups,'results/group_spreaders.png')
        plotNearSubject(near,'results/near_subject.png',stats['subjectHeardAtStep'],p['nearRadius'])
        plotTree(agents,'results/tree.png')
        print('final counts:',counts[-1],'transmission:',stats,'seconds:',time.perf_counter()-start)
    else:
        from viewer_friendships import runViewer
        agents,history = runViewer(build,args.steps,p,rumour)
        print('stopped at step',len(history),'transmission:',transmissionStats(agents))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
