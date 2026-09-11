"""Held-out flights and causal controls, kept separate from the showcase."""
import runtime
import json
import numpy as np
from brain import FlyBrain
from simulate import rollout

ROOT=runtime.ROOT

def main():
    brain=FlyBrain();model=dict(np.load(ROOT/'data/readout.npz'))
    conditions=[dict(east=24,heading=-.01,altitude=76),
                dict(east=-25,heading=.015,altitude=78),
                dict(east=40,heading=-.02,altitude=80)]
    results=[]
    for condition in conditions:
        for mode in ['teacher','neural','disconnected']:
            r=rollout(brain,model,mode=mode,**condition)
            results.append({k:v for k,v in r.items() if k!='frames'})
    (ROOT/'outputs/validation.json').write_text(json.dumps(results,indent=2))
    for mode in ['teacher','neural','disconnected']:
        rr=[r for r in results if r['mode']==mode]
        print(mode,sum(r['landed'] for r in rr),'/',len(rr),'successful landings')

if __name__=='__main__':main()
