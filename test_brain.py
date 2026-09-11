"""Small synthetic fixtures test mechanics only; never used in the showcase."""
import gzip
import json
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np
from brain import FlyBrain

class BrainTests(unittest.TestCase):
    def make_fixture(self,path):
        n=40
        edges=[(i,i+20,1.0 if i%2 else -1.0) for i in range(20)]
        b=struct.pack('<II',n,len(edges))
        b+=b''.join(struct.pack('<IIf',*e) for e in edges)
        b+=b''.join(struct.pack('<BH',0 if i<20 else 1,0 if i<20 else 2) for i in range(n))
        (path/'connectome.bin.gz').write_bytes(gzip.compress(b))
        (path/'neuron_meta.json').write_text(json.dumps({'groups':[{'id':0,'name':'visual'},{'id':2,'name':'central'}]}))

    def test_real_edges_are_required_for_readout_signal(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.make_fixture(p);b=FlyBrain(data_dir=p)
            self.assertFalse(set(b.input_ids)&set(b.readout_ids))
            connected=b.step(np.ones(10)*.5,iterations=16)
            b.reset();disconnected=b.step(np.ones(10)*.5,iterations=16,disconnect=True)
            self.assertGreater(np.linalg.norm(connected),.1)
            np.testing.assert_array_equal(disconnected,np.zeros_like(disconnected))

    def test_batch_and_single_converge_to_same_state(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.make_fixture(p);b=FlyBrain(data_dir=p)
            x=np.linspace(-.4,.5,10,dtype=np.float32)
            expected=b.batch_features(x[None],iterations=20)[0]
            actual=b.step(x,iterations=20)
            np.testing.assert_allclose(expected,actual,atol=1e-6)

    def test_bad_binary_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);self.make_fixture(p)
            b=gzip.decompress((p/'connectome.bin.gz').read_bytes())
            (p/'connectome.bin.gz').write_bytes(gzip.compress(b[:-1]))
            with self.assertRaises(ValueError):FlyBrain(data_dir=p)

if __name__=='__main__':unittest.main()
