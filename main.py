"""Team Char Siu: command-line entry point. Importing does not start a run."""
import argparse
import math
import time
from pathlib import Path


def positiveInt(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return number


def parseArgs(argv=None):
    parser = argparse.ArgumentParser(description='Team Char Siu rumour simulation')
    parser.add_argument('rumour', nargs='?', default=None)
    parser.add_argument('--n', type=positiveInt, default=500)
    parser.add_argument('--steps', type=positiveInt, default=400)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args(argv)
    if not 0 <= args.seed < 2**32:
        parser.error('--seed must be between 0 and 4294967295')
    return args


def makeSettings(n):
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError('population must be a positive integer')
    return dict(stepSize=1.5, contactRadius=4*math.sqrt(500/n), rumourStrength=0.06,
        correctionStrength=0.03, correctionStart=60, correctionSeeds=0,
        minInterest=0.5, subjectDenies=1., avoidRadius=7, avoidChance=0.75,
        noticeAfter=20, nearRadius=10, leash=15, travelChance=0.003,
        travelSpeed=2., stayLength=40)


def buildAgents(n, seed, settings):
    from simulation import makeAgents, seedSpreaders, pickSubject
    agents = makeAgents(n, seed, 0.2, settings['leash'])
    seedSpreaders(agents, 1, 0)
    return pickSubject(agents, 3, friendCount=12, lingerCount=4,
                       friendRadius=min(4, settings['avoidRadius']*0.7))


def main(argv=None):
    args = parseArgs(argv)
    rumour = args.rumour
    if rumour is None:
        rumour = input('Type the rumour (enter for default): ').strip()
    rumour = rumour or 'The canteen is closing next week'
    settings = makeSettings(args.n)
    def build():
        return buildAgents(args.n, args.seed, settings)
    try:
        agents = build()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    from simulation import runSimulation, transmissionStats
    if args.headless:
        from plots import plotCurve, plotGroupSpreaders, plotNearSubject, plotTree
        Path('results').mkdir(exist_ok=True)
        start = time.perf_counter()
        counts, groups, near = runSimulation(agents, args.steps, settings)
        seconds = time.perf_counter()-start
        stats = transmissionStats(agents)
        plotCurve(counts, 'results/curve.png', rumour)
        plotGroupSpreaders(groups, 'results/group_spreaders.png')
        plotNearSubject(near, 'results/near_subject.png', stats['subjectHeardAtStep'], settings['nearRadius'])
        plotTree(agents, 'results/tree.png')
        print('seed:', args.seed, 'n:', args.n, 'steps:', args.steps)
        print('final counts [unaware, spreader, corrector, stifler]:', counts[-1])
        print('transmission:', stats)
        print('run time: %.2f s' % seconds)
    else:
        from viewer_friendships import runViewer
        agents, history = runViewer(build, args.steps, settings, rumour)
        print('stopped at step', len(history), 'transmission:', transmissionStats(agents))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
