"""Agent visibility checks without a graphics context."""
import ast
import math
from pathlib import Path
import unittest

class AgentVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.tree = ast.parse((Path(__file__).resolve().parents[1]/'viewer_friendships.py').read_text())
    def test_diamond_has_four_distinct_corners(self):
        node = next(n for n in self.tree.body if isinstance(n,ast.FunctionDef) and n.name == 'diamondPoints')
        ns = dict(math=math)
        exec(compile(ast.Module(body=[node],type_ignores=[]),'diamond','exec'),ns)
        points = ns['diamondPoints'](100,200,3.25)
        self.assertEqual(len(set(points)),4)
        self.assertGreater(points[0][1],200)
        self.assertGreater(points[1][0],100)
        self.assertLess(points[2][1],200)
        self.assertLess(points[3][0],100)
        self.assertTrue(all(abs(math.dist(p,(100,200))-3.25*1.5/math.sqrt(2)) < 1e-9 for p in points))
    def test_modest_size_increase(self):
        sizes = {}
        for node in ast.walk(self.tree):
            if isinstance(node,ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target,ast.Attribute) and target.attr in ('DOT_IDLE','DOT_ACTIVE','DOT_HOP'):
                    sizes[target.attr] = ast.literal_eval(node.value)
        self.assertEqual(sizes,dict(DOT_IDLE=3.25,DOT_ACTIVE=5.75,DOT_HOP=4.75))
    def test_outline_depends_on_membership(self):
        branch = next(n for n in ast.walk(self.tree) if isinstance(n,ast.If) and ast.unparse(n.test) == 'a.group == NO_GROUP')
        calls = [n for n in ast.walk(branch) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        self.assertTrue(any(n.func.attr == 'draw_polygon_outline' for n in calls))
        self.assertFalse(any(isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and t.attr == 'group' for t in n.targets) for n in ast.walk(self.tree)))
