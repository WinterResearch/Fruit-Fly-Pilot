"""Fixed, signed, sparse rate network on a FlyWire-derived graph.

This is an engineering model, not the Shiu spiking model or a faithful animal
emulation. All imported nodes/edges are retained. Input electrodes, incoming
weight normalization, tanh dynamics, and the trained readout are our choices.
"""
import runtime
import gzip
import hashlib
import json
import struct
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix

ROOT = runtime.ROOT

class FlyBrain:
    def __init__(self, seed=71, data_dir=None, gain=0.8):
        data_dir = Path(data_dir or ROOT / 'data')
        path = data_dir / 'connectome.bin.gz'
        if not path.exists():
            raise FileNotFoundError('Real connectome missing. Run download-deps.ps1; no synthetic fallback is used.')
        compressed = path.read_bytes()
        self.sha256 = hashlib.sha256(compressed).hexdigest()
        raw = gzip.decompress(compressed)
        self.n, self.e = struct.unpack_from('<II', raw)
        expected = 8 + 12 * self.e + 3 * self.n
        if len(raw) != expected:
            raise ValueError(f'Bad connectome length: {len(raw)} != {expected}')
        edges = np.frombuffer(raw, dtype=[('pre','<u4'), ('post','<u4'), ('w','<f4')], count=self.e, offset=8)
        if edges['pre'].max() >= self.n or edges['post'].max() >= self.n or not np.isfinite(edges['w']).all():
            raise ValueError('Invalid edge index or weight')
        metadata = np.frombuffer(raw, dtype=[('region','u1'), ('group','<u2')], count=self.n, offset=8+12*self.e)
        self.groups = metadata['group'].copy()
        self.regions = metadata['region'].copy()
        self.meta = json.loads((data_dir/'neuron_meta.json').read_text(encoding='utf-8-sig'))
        self.group_names = {g['id']:g['name'] for g in self.meta['groups']}
        self.W = csr_matrix((edges['w'], (edges['post'], edges['pre'])), shape=(self.n,self.n), dtype=np.float32)
        incoming = np.asarray(abs(self.W).sum(axis=1)).ravel()
        self.W.data *= np.repeat(gain / np.maximum(incoming, 1), np.diff(self.W.indptr))
        self.gain = gain
        self.state = np.zeros(self.n, np.float32)
        self.rng = np.random.default_rng(seed)
        # Synthetic electrodes partition the upstream visual group. They do not
        # assert an anatomical retinotopy or a natural instrument-reading ability.
        self.input_ids = np.flatnonzero(self.groups == 0)
        self.input_channels = self.rng.permutation(len(self.input_ids)) % 20
        self.input_scale = self.rng.uniform(0.7, 1.3, len(self.input_ids)).astype(np.float32)
        self.input_bias = self.rng.uniform(-0.2, 0.2, len(self.input_ids)).astype(np.float32)
        # Read from cells with a real incoming edge from the driven visual set.
        # Exclude the injected cells: disconnecting edges removes their signal.
        strength = np.asarray(abs(self.W[:,self.input_ids]).sum(axis=1)).ravel()
        strength[self.input_ids] = 0
        candidates = np.flatnonzero(strength > 0.015)
        if len(candidates) < 256:
            candidates = np.flatnonzero(strength > 0)
        self.readout_ids = self.rng.choice(candidates, min(512,len(candidates)), replace=False)
        self.sample_ids = np.linspace(0,self.n-1,384,dtype=int)
        self.steps = 0

    def reset(self):
        self.state.fill(0)
        self.steps = 0

    def encode(self, observations):
        x = np.asarray(observations,dtype=np.float32)
        # 10 instrument channels, paired positive/negative stimulation.
        return np.concatenate((x,-x),axis=-1)

    def step(self, observations, iterations=6, disconnect=False):
        channels = self.encode(observations)
        current = self.input_scale * channels[self.input_channels] + self.input_bias
        for _ in range(iterations):
            recurrent = np.zeros_like(self.state) if disconnect else self.W @ self.state
            recurrent[self.input_ids] += current
            self.state += 0.65 * (np.tanh(recurrent) - self.state)
            self.steps += 1
        return self.state[self.readout_ids].copy()

    def batch_features(self, observations, iterations=12, batch_size=32):
        result=[]
        for start in range(0,len(observations),batch_size):
            x=np.asarray(observations[start:start+batch_size],np.float32)
            channels=self.encode(x)
            current=(channels[:,self.input_channels]*self.input_scale+self.input_bias).T
            states=np.zeros((self.n,len(x)),np.float32)
            for _ in range(iterations):
                recurrent=self.W @ states
                recurrent[self.input_ids] += current
                states += 0.65*(np.tanh(recurrent)-states)
            result.append(states[self.readout_ids].T.copy())
        return np.concatenate(result)

    def telemetry(self):
        # Rate activation, explicitly not spikes, dopamine, or measured emotion.
        a=np.abs(self.state)
        return {'active':int(np.count_nonzero(a>.01)), 'mean':float(a.mean()),
                'sample':np.round(self.state[self.sample_ids],4).tolist(),
                'regions':[float(a[self.regions==i].mean()) if np.any(self.regions==i) else 0.0 for i in range(4)]}

