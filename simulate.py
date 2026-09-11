"""Train a neural readout and record actual JSBSim flight attempts."""
import runtime
import argparse
import json
import time
from pathlib import Path
import numpy as np
from brain import FlyBrain
from flight import Aircraft

ROOT=runtime.ROOT

def fit(brain,teacher,samples=1024):
    rng=np.random.default_rng(124)
    obs=rng.uniform(-1.1,1.1,(samples,10)).astype(np.float32)
    obs[:,8]=rng.uniform(0,1.5,samples)
    desired=np.asarray([teacher.reference(x) for x in obs])
    print(f'Encoding {samples} demonstrations through {brain.n:,} neurons...',flush=True)
    start=time.perf_counter()
    features=brain.batch_features(obs)
    print(f'Neural features computed in {time.perf_counter()-start:.1f}s',flush=True)
    mean=features.mean(0);scale=np.maximum(features.std(0),.002)
    X=np.column_stack(((features-mean)/scale,np.ones(samples)))
    # Small linear adapter. No raw observation skip connection.
    reg=np.eye(X.shape[1])*.15;reg[-1,-1]=.001
    weights=np.linalg.solve(X.T@X+reg,X.T@desired)
    pred=X@weights
    print('Imitation train RMSE:',np.sqrt(np.mean((pred-desired)**2,axis=0)),flush=True)
    model=dict(mean=mean,scale=scale,weights=weights)
    np.savez(ROOT/'data/readout.npz',**model)
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs/training.json').write_text(json.dumps(dict(samples=samples,seed=124,
        method='ridge imitation of attitude-control teacher; fixed connectome',
        training_rmse=np.sqrt(np.mean((pred-desired)**2,axis=0)).tolist(),
        connectome_sha256=brain.sha256,neurons=brain.n,edges=brain.e),indent=2))
    return model

def rollout(brain,model,mode='neural',east=32,altitude=78,north=-1300,heading=.02,wind=0,max_time=65):
    plane=Aircraft(east=east,altitude=altitude,north=north,heading=heading,wind=wind)
    brain.reset();frames=[];start=time.perf_counter();last_neural={}
    while plane.t<max_time:
        s=plane.state();obs=plane.observations(s)
        if mode=='teacher':action=plane.reference(obs)
        else:
            features=brain.step(obs,disconnect=mode=='disconnected')
            X=np.append((features-model['mean'])/model['scale'],1)
            action=np.clip(X@model['weights'],-.85,.85)
            last_neural=brain.telemetry()
        s['neural']=last_neural;frames.append(s)
        plane.advance(action)
        if plane.touchdown is not None and plane.t>plane.touchdown['t']+7:break
        if abs(s['phi'])>1.4 or s['alt']<-.5 or not np.isfinite(list(obs)).all():break
    td=plane.touchdown
    landed=bool(td and abs(td['lateral_error'])<18 and 0<td['north']<1800 and td['sink_rate']<3 and abs(td['roll'])<.15)
    result=dict(mode=mode,landed=landed,neurons=brain.n,edges=brain.e,connectome_sha256=brain.sha256,
        physics='JSBSim c172p',neural_model='fixed signed normalized rate network; tanh activation',
        assistance=['geometric approach director','throttle speed hold','post-touchdown brakes'],
        inputs='synthetic instrument-to-visual-population electrodes; not reconstructed retinal vision',
        training='ridge imitation of attitude controller; no reinforcement learning',
        touchdown_time=td['t'] if td else None,result=td,frames=frames,playback_rate=1.5,
        wall_seconds=time.perf_counter()-start,initial=dict(east=east,altitude=altitude,north=north,heading=heading,wind=wind))
    print(mode,'landed=',landed,'touchdown=',td,'elapsed=',round(result['wall_seconds'],2),flush=True)
    return result

def save(result,name='flight'):
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs'/f'{name}.json').write_text(json.dumps(result,separators=(',',':')))
    if name=='flight':(ROOT/'web/replay.js').write_text('window.FLIGHT_DATA = '+json.dumps(result,separators=(',',':'))+';\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('--train',action='store_true');p.add_argument('--samples',type=int,default=1024);p.add_argument('--mode',choices=['neural','teacher','disconnected'],default='neural');p.add_argument('--east',type=float,default=32);p.add_argument('--altitude',type=float,default=78);p.add_argument('--north',type=float,default=-1300);p.add_argument('--heading',type=float,default=.02);p.add_argument('--name',default='flight');args=p.parse_args()
    brain=FlyBrain();print('Loaded',brain.n,'neurons;',brain.e,'edges',flush=True)
    if args.train:model=fit(brain,Aircraft(),args.samples)
    elif (ROOT/'data/readout.npz').exists():model=dict(np.load(ROOT/'data/readout.npz'))
    elif args.mode=='teacher':model={}
    else:raise SystemExit('Train first: python simulate.py --train')
    result=rollout(brain,model,mode=args.mode,east=args.east,altitude=args.altitude,north=args.north,heading=args.heading)
    save(result,args.name)

if __name__=='__main__':main()
