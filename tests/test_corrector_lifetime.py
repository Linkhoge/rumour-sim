"""Regression tests for persistent correction; no Arcade installation required."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent import Agent, UNAWARE, SPREADER, CORRECTOR, STIFLER, HOW_LONG


class CorrectorLifetimeTests(unittest.TestCase):
    def agent(self):
        return Agent(50, 50, UNAWARE, 0.5, 0)

    def test_corrector_persists_after_1000_ticks(self):
        a = self.agent()
        a.becomeCorrector(3, 1, 10)
        for _ in range(1000):
            a.tick()
        self.assertEqual(a.state, CORRECTOR)
        self.assertFalse(a.believed or a.avoiding)
        self.assertEqual((a.corrSource, a.corrGeneration, a.changedAt), (3, 1, 10))

    def test_subject_corrector_persists(self):
        a = self.agent()
        a.isSubject = True
        a.becomeSubjectCorrector(-1, -1, 20)
        for _ in range(400):
            a.tick()
        self.assertEqual(a.state, CORRECTOR)
        self.assertEqual(a.heardAt, 20)

    def test_spreader_still_expires(self):
        a = self.agent()
        a.becomeSpreader()
        for _ in range(HOW_LONG - 1):
            a.tick()
        self.assertEqual(a.state, SPREADER)
        a.tick()
        self.assertEqual(a.state, STIFLER)
        self.assertTrue(a.believed)


if __name__ == '__main__':
    unittest.main()
