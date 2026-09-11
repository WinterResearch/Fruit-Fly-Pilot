"""JSBSim C172 approach with disclosed guidance and throttle assistance.

The neural controller closes roll/pitch attitude loops. An engineered approach
director supplies desired attitudes from runway geometry (like flight-director
bars); a separate speed hold supplies throttle. These are substantial assists.
"""
import runtime
import math
from pathlib import Path
import numpy as np

FT=0.3048
RAD=math.pi/180
EARTH=6378137.0
DT=1/60

class Aircraft:
    def __init__(self, east=32, altitude=78, north=-1300, heading=0.02, wind=0):
        import jsbsim
        self.fdm=jsbsim.FGFDMExec(str(Path(jsbsim.__file__).parent))
        self.fdm.set_debug_level(0)
        self.fdm.load_model('c172p')
        self.fdm.set_dt(DT)
        self.lat0=37.6*RAD
        self.lon0=-122.4*RAD
        initial={
            'ic/lat-geod-deg':(self.lat0+north/EARTH)/RAD,
            'ic/long-gc-deg':(self.lon0+east/(EARTH*math.cos(self.lat0)))/RAD,
            'ic/h-sl-ft':altitude/FT,
            'ic/terrain-elevation-ft':0,
            'ic/vc-kts':65,
            'ic/gamma-deg':-3,
            'ic/psi-true-deg':heading/RAD,
            'fcs/flap-cmd-norm':0.33333,
            'fcs/mixture-cmd-norm':1,
            'propulsion/set-running':-1,
        }
        for k,v in initial.items():self.fdm[k]=v
        self.fdm.run_ic()
        self.fdm['propulsion/set-running']=-1
        try:self.fdm.do_trim(0)
        except Exception:pass
        self.trim_elevator=float(self.fdm['fcs/elevator-cmd-norm'])
        self.trim_theta=float(self.fdm['attitude/theta-rad'])
        self.trim_throttle=float(self.fdm['fcs/throttle-cmd-norm'])
        self.fdm['atmosphere/wind-east-fps']=wind/FT
        self.t=0.0
        self.touchdown=None
        self.control=[0, self.trim_elevator, self.trim_throttle]

    def state(self):
        p=self.fdm
        lat=p['position/lat-geod-rad'];lon=p['position/long-gc-rad']
        h=float(p['position/h-agl-ft'])*FT
        return dict(t=self.t,north=(lat-self.lat0)*EARTH,east=(lon-self.lon0)*EARTH*math.cos(self.lat0),
                    alt=h,phi=float(p['attitude/phi-rad']),theta=float(p['attitude/theta-rad']),
                    heading=math.atan2(math.sin(p['attitude/psi-rad']),math.cos(p['attitude/psi-rad'])),
                    course=math.atan2(p['velocities/v-east-fps'],p['velocities/v-north-fps']),
                    airspeed=float(p['velocities/vc-kts']),vs=-float(p['velocities/v-down-fps'])*FT,
                    p=float(p['velocities/p-rad_sec']),q=float(p['velocities/q-rad_sec']),
                    controls=list(self.control))

    def observations(self,s=None):
        s=s or self.state()
        # The flight director is explicit assistance, not hidden neural behavior.
        desired_heading=np.clip(-s['east']/280,-.20,.20)
        desired_roll=np.clip(1.5*(desired_heading-s['course']),-.23,.23)
        target_alt=max(1.0,(-s['north']+90)*math.tan(3*RAD))
        gamma=-3*RAD+np.clip((target_alt-s['alt'])*.006,-.05,.05)
        if s['alt']<9:
            gamma=-.007-.004*s['alt']
        alpha=self.trim_theta+3*RAD
        desired_pitch=np.clip(alpha+gamma,-.02,.15)
        if s['alt']<9:
            desired_pitch+=.13*(1-max(0,s['alt'])/9)
        return np.array([
            np.clip((desired_roll-s['phi'])/.3,-2,2),
            np.clip(s['p']/.4,-2,2),
            np.clip((desired_pitch-s['theta'])/.12,-2,2),
            np.clip(s['q']/.3,-2,2),
            np.clip((65-s['airspeed'])/20,-2,2),
            np.clip(s['east']/150,-2,2),
            np.clip(s['heading']/.3,-2,2),
            np.clip((target_alt-s['alt'])/50,-2,2),
            np.clip(s['alt']/100,0,2),
            np.clip(s['vs']/5,-2,2),
        ],np.float32)

    def reference(self,obs):
        # Teacher used only for demonstration generation / adapter calibration.
        return np.array([np.clip(.85*obs[0]-.22*obs[1],-.85,.85),
                         np.clip(self.trim_elevator-.40*obs[2]+.16*obs[3],-.8,.8)],np.float32)

    def advance(self,action,substeps=6):
        s=self.state()
        throttle=np.clip(self.trim_throttle+.045*(65-s['airspeed']),.08,.85)
        if s['alt']<6:throttle=min(throttle,.08)
        if self.touchdown is not None:throttle=0
        self.control=[float(np.clip(action[0],-1,1)),float(np.clip(action[1],-1,1)),float(throttle)]
        for _ in range(substeps):
            p=self.fdm
            p['fcs/aileron-cmd-norm']=self.control[0]
            p['fcs/elevator-cmd-norm']=self.control[1]
            p['fcs/throttle-cmd-norm']=self.control[2]
            if self.touchdown is not None:
                p['fcs/left-brake-cmd-norm']=.35;p['fcs/right-brake-cmd-norm']=.35
            before=self.state()
            if not p.run():raise RuntimeError('JSBSim stopped')
            self.t+=DT
            after=self.state()
            contact=[i for i in range(3) if p[f'gear/unit[{i}]/WOW']]
            if self.touchdown is None and contact:
                self.touchdown=dict(t=self.t,sink_rate=max(0,-before['vs']),lateral_error=after['east'],north=after['north'],roll=after['phi'],cg_height=after['alt'],contact_units=contact)
        return self.state()
