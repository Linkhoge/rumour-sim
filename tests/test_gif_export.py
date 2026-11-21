"""GIF capture, synchronisation and file-output regressions."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
from gif_export import recordRun,saveGif,snapshot


def agents():
    return [SimpleNamespace(x=20.+i*10,y=30.,state=1 if i == 0 else 0,infector=-1,group=0 if i%2 else -1,
        isFriend=i == 1,wasFriend=i == 1,avoiding=False,believed=i == 0,isSubject=i == 3,corrGeneration=-1) for i in range(4)]


def step(items,t,p):
    for a in items:
        a.x += np.random.random()
    if t < 3:
        items[t+1].state = 1
        items[t+1].infector = 0
        items[t+1].believed = True


def counts(items):
    return [sum(a.state == k for a in items) for k in range(4)]


def modules():
    return dict(simulation=SimpleNamespace(stepSimulation=step,countStates=counts,
        countSpreadersByGroup=lambda items:[0,sum(a.state == 1 for a in items),0,0,0],
        nearSubject=lambda items,r:[3,sum(a.believed for a in items if not a.isSubject)]),
        movement=SimpleNamespace(GROUP_CENTRES=[(33,33),(67,33),(33,67),(67,67)]))


class GifTests(unittest.TestCase):
    def test_recording_preserves_rng_and_results(self):
        baseline,recorded = agents(),agents()
        np.random.seed(42)
        expected = []
        for t in range(5):
            step(baseline,t,{})
            expected.append(counts(baseline))
        nextRandom = np.random.random()
        np.random.seed(42)
        with patch.dict(sys.modules,modules()):
            run = recordRun(recorded,5,{},every=2)
        np.testing.assert_array_equal(run['counts'][1:],expected)
        self.assertEqual([(a.x,a.state) for a in baseline],[(a.x,a.state) for a in recorded])
        self.assertEqual(np.random.random(),nextRandom)
        self.assertEqual([f['step'] for f in run['frames']],[0,2,4,5])
    def test_snapshot_is_independent(self):
        items = agents()
        saved = snapshot(items,0)
        items[0].x = 99
        items[0].state = 3
        self.assertEqual(saved['positions'][0,0],20)
        self.assertEqual(saved['states'][0],1)
    def test_gif_and_metadata(self):
        p = dict(leash=15,avoidRadius=7,nearRadius=10)
        with patch.dict(sys.modules,modules()):
            run = recordRun(agents(),5,p,every=2)
        with tempfile.TemporaryDirectory() as folder:
            path = saveGif(run,Path(folder)/'test.gif','GIF regression',fps=5,width=480,seed=42)
            with Image.open(path) as image:
                self.assertEqual(image.format,'GIF')
                self.assertEqual(image.size,(480,312))
                self.assertEqual(image.n_frames,4)
            meta = json.loads(path.with_suffix('.json').read_text())
            self.assertEqual(meta['frame_steps'],[0,2,4,5])
            self.assertEqual(meta['seed'],42)
    def test_invalid_record_interval(self):
        with patch.dict(sys.modules,modules()),self.assertRaises(ValueError):
            recordRun(agents(),5,{},every=0)
