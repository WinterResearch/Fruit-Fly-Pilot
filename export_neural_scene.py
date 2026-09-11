"""Record a larger, connected neuron subset for the 3D activity visualization.

Selection and display coordinates do not change the controller. Coordinates
are schematic, grouped by upstream annotations, not reconstructed anatomy.
"""
import runtime
import json
import numpy as np
from brain import FlyBrain
from simulate import rollout

ROOT = runtime.ROOT

def main():
    brain = FlyBrain()
    rng = np.random.default_rng(181)
    # Include every actual readout cell and sample their presynaptic neighbors.
    incoming = brain.W[brain.readout_ids].tocoo()
    strength = np.bincount(incoming.col, weights=np.abs(incoming.data), minlength=brain.n)
    strongest = np.argsort(strength)[-1000:]
    visual = rng.choice(brain.input_ids, 1000, replace=False)
    other = np.flatnonzero((brain.groups != 0) & (strength > 0))
    other = rng.choice(other, min(600, len(other)), replace=False)
    ids = np.unique(np.concatenate((brain.readout_ids, strongest, visual, other)))
    sub = brain.W[ids][:, ids].tocoo()
    # Stored orientation: source -> target. Preserve actual mapped edges only.
    candidates = np.flatnonzero(sub.row != sub.col)
    chosen = candidates[np.argsort(np.abs(sub.data[candidates]))[-6500:]]
    edges = np.column_stack((sub.col[chosen], sub.row[chosen])).tolist()
    brain.sample_ids = ids
    result = rollout(brain, dict(np.load(ROOT/'data/readout.npz')))
    original = json.loads((ROOT/'outputs/flight.json').read_text())
    assert len(result['frames']) == len(original['frames'])
    for a, b in zip(result['frames'], original['frames']):
        assert np.allclose(a['controls'], b['controls'], atol=1e-10)
    # Grouped 3D clouds with mild spatial separation; this is a visualization.
    groups = brain.groups[ids]
    unique = sorted(set(int(g) for g in groups))
    centers = {}
    for k, g in enumerate(unique):
        angle = k*2.399963
        centers[g] = np.array([np.cos(angle)*2, np.sin(angle)*1.2, np.sin(angle*.7)*.7])
    centers[0] = np.array([-1.6, .05, 0])
    # Common large population opposite the visual input cluster.
    if 2 in centers:
        centers[2] = np.array([1.35, .1, 0])
    positions = []
    for g in groups:
        direction = rng.normal(size=3)
        direction /= np.linalg.norm(direction)
        radius = rng.random()**(1/3)
        scale = np.array([1.05,.92,.85]) if g in (0,2) else np.array([.34,.31,.3])
        positions.append((centers[int(g)]+direction*radius*scale).tolist())
    payload = dict(ids=ids.tolist(), groups=groups.tolist(), positions=positions, edges=edges,
                   readout=np.isin(ids,brain.readout_ids).tolist(), input=np.isin(ids,brain.input_ids).tolist(),
                   frames=[dict(t=f['t'],activity=f['neural']['sample'],controls=f['controls']) for f in result['frames']],
                   touchdown_time=result['touchdown_time'], source_sha256=brain.sha256,
                   layout='Schematic 3D grouping; not anatomical coordinates',
                   activity='Recorded signed rate-model activations; not biological spikes')
    (ROOT/'outputs/neural-scene.json').write_text(json.dumps(payload,separators=(',',':')))
    (ROOT/'web/neural-data.js').write_text('window.NEURAL_DATA='+json.dumps(payload,separators=(',',':'))+';\n')
    print(f'Saved {len(ids)} neurons, {len(edges)} real edges; flight controls exactly matched.',flush=True)

if __name__ == '__main__':
    main()
