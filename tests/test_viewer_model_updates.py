"""Repair regressions, independent of a graphics context."""
import ast
from pathlib import Path
import unittest
from agent import Agent,UNAWARE,CORRECTOR,STIFLER
from main import makeSettings,parseArgs
import movement
from simulation import rollSpread
class RepairTests(unittest.TestCase):
    def test_settings(self):
        p = makeSettings(500)
        self.assertEqual((p['correctionStrength'],p['correctionDuration'],p['correctionRadius']),(.004,110,6))
        self.assertEqual(parseArgs(['--correction-strength=0']).correction_strength,0)
    def test_spacing(self):
        centres = movement.GROUP_CENTRES
        movement.configureGroups(24)
        self.assertEqual(centres[0],(24,24))
        movement.configureGroups(25)
    def test_no_count_cap(self):
        agents = [Agent(50,50,UNAWARE,1,0) for _ in range(70)]
        agents[0].becomeCorrector()
        for a in agents:
            a.openness = 1
        rollSpread(agents,1,4,0,1)
        self.assertEqual(sum(a.state == CORRECTOR for a in agents),70)
    def test_no_reactivation(self):
        a,b = [Agent(50,50,UNAWARE,1,0) for _ in range(2)]
        a.becomeCorrector()
        b.becomeCorrector()
        b.state,b.openness = STIFLER,1
        rollSpread([a,b],1,4,0,1)
        self.assertEqual(b.state,STIFLER)
    def test_ignore_branch(self):
        a,b = [Agent(50,50,UNAWARE,1,0) for _ in range(2)]
        a.becomeSpreader()
        b.isSubject = True
        rollSpread([a,b],1,4,1,0,subjectDenies=0)
        self.assertTrue(b.ignored)
    def test_colours_and_layout(self):
        tree = ast.parse((Path(__file__).resolve().parents[1]/'viewer_arcade.py').read_text())
        body = [n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef) and n.name == 'nodeColour']
        ns = dict(STIFLER=STIFLER)
        exec(compile(ast.Module(body=body,type_ignores=[]),'styles','exec'),ns)
        a = Agent(0,0,UNAWARE,1,0)
        a.wasFriend = True
        self.assertEqual(ns['nodeColour'](a),ns['EX_FRIEND_COL'])
        self.assertEqual((ns['SIDE'],ns['CHART_HEIGHT']),(440,280))
    def test_nonfinite_settings_rejected(self):
        with self.assertRaises(ValueError):
            makeSettings(500,correctionStrength=float('nan'))
