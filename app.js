/* Original procedural scene. No downloaded art, fonts, audio, or game assets. */
(() => {
'use strict';
const fail = text => {const e=document.getElementById('error');e.hidden=false;e.textContent=text;};
if(!window.THREE){fail('Three.js is missing. Run download-deps.ps1 and bootstrap_offline.py.');return;}
if(!window.FLIGHT_DATA){fail('The scene is ready for a flight. Run simulate.py to generate a real controller rollout, then reopen this file.');return;}
const T=window.THREE,D=window.FLIGHT_DATA;
const capture=new URLSearchParams(location.search).has('capture');
if(capture)document.body.classList.add('capture');
const scene=new T.Scene();scene.background=new T.Color('#a6bbc0');scene.fog=new T.FogExp2('#b0b9ae',.00017);
const renderer=new T.WebGLRenderer({canvas:document.querySelector('#scene'),antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(1);renderer.setSize(1280,720,false);renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.12;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
const pilotRenderer=new T.WebGLRenderer({canvas:document.querySelector('#pilot-cam'),antialias:true,preserveDrawingBuffer:true});
pilotRenderer.setSize(544,312,false);pilotRenderer.outputColorSpace=T.SRGBColorSpace;pilotRenderer.toneMapping=T.ACESFilmicToneMapping;pilotRenderer.toneMappingExposure=1.3;
const camera=new T.PerspectiveCamera(58,1280/720,.04,20000),pilotCamera=new T.PerspectiveCamera(49,544/312,.03,10000);
const hemi=new T.HemisphereLight('#c6e4f0','#716246',2.0);scene.add(hemi);
const sun=new T.DirectionalLight('#ffe0aa',3.2);sun.position.set(-200,300,-500);scene.add(sun);scene.add(sun.target);
const fill=new T.DirectionalLight('#b0d9ed',.8);fill.position.set(10,5,10);scene.add(fill);
const aircraft=new T.Group();scene.add(aircraft);
const materials={};
function mat(color,rough=.7,metal=0){const k=color+rough+metal;return materials[k]||(materials[k]=new T.MeshStandardMaterial({color,roughness:rough,metalness:metal}));}
function mesh(geometry,material,parent=aircraft){const m=new T.Mesh(geometry,material);parent.add(m);return m;}
function box(x,y,z,w,h,d,color,parent=aircraft){const m=mesh(new T.BoxGeometry(w,h,d),typeof color==='string'?mat(color):color,parent);m.position.set(x,y,z);return m;}
function ell(x,y,z,sx,sy,sz,color,parent=aircraft,segments=24){const m=mesh(new T.SphereGeometry(1,segments,16),typeof color==='string'?mat(color):color,parent);m.position.set(x,y,z);m.scale.set(sx,sy,sz);return m;}
function link(a,b,r,color,parent=aircraft){const m=mesh(new T.CylinderGeometry(r,r,1,9),typeof color==='string'?mat(color):color,parent);setLink(m,a,b);return m;}
function setLink(m,a,b){a=new T.Vector3(...a);b=new T.Vector3(...b);const delta=b.clone().sub(a);m.position.copy(a).add(b).multiplyScalar(.5);m.scale.y=delta.length();m.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),delta.normalize());}
function label(text,w,h,background='#162a33',foreground='#e4d9b6',size=34){const c=document.createElement('canvas');c.width=512;c.height=128;const x=c.getContext('2d');x.fillStyle=background;x.fillRect(0,0,512,128);x.fillStyle=foreground;x.font=`bold ${size}px Arial`;x.textAlign='center';x.textBaseline='middle';x.fillText(text,256,64);const texture=new T.CanvasTexture(c);texture.colorSpace=T.SRGBColorSpace;return new T.Mesh(new T.PlaneGeometry(w,h),new T.MeshBasicMaterial({map:texture}));}
function planeLabel(text,x,y,z,w,h,parent=aircraft){const m=label(text,w,h);m.position.set(x,y,z);parent.add(m);return m;}
let seed=7391;function rand(){seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;}

// Coastal airfield: runway and landmarks have fixed world positions.
const ground=mesh(new T.PlaneGeometry(40000,40000),mat('#5d7053'),scene);ground.rotation.x=-Math.PI/2;ground.position.y=-.1;
const water=mesh(new T.PlaneGeometry(14000,22000),mat('#688f96',.3,.15),scene);water.rotation.x=-Math.PI/2;water.position.set(-8200,-.06,-2000);
for(let i=0;i<140;i++){const x=(rand()-.5)*10000,z=(rand()-.5)*13000;const m=box(x,.005,z,250+rand()*650,.02,300+rand()*800,['#687957','#7b865e','#596d4d','#88936b'][i%4],scene);m.rotation.y=rand()*.08;}
const runway=box(0,0,-900,36,.06,1800,'#42484a',scene);
box(-19,.02,-900,1,.07,1800,'#b9b8a2',scene);box(19,.02,-900,1,.07,1800,'#b9b8a2',scene);
for(let n=0;n<30;n++){box(0,.045,-(40+n*60),.65,.08,26,'#edead8',scene);}
for(let side of [-1,1])for(let i=0;i<5;i++){box(side*(3+i*2.6),.05,-28,1.5,.09,28,'#edead8',scene);}
const rn=label('36',12,14,'#42484a','#efefdf',83);rn.rotation.x=-Math.PI/2;rn.position.set(0,.105,-64);scene.add(rn);
for(let z=20;z<650;z+=40){box(0,.4,z,.22,.6,.22,'#bfba9d',scene);ell(0,.8,z,.24,.16,.24,new T.MeshBasicMaterial({color:'#fff1ba'}),scene,8);if(z<160)for(let x of [-8,-4,4,8])ell(x,.6,z,.22,.15,.22,new T.MeshBasicMaterial({color:'#fff1ba'}),scene,8);}
for(let z=0;z>-1800;z-=60)for(let x of [-21,21]){ell(x,.2,z,.18,.14,.18,new T.MeshBasicMaterial({color:'#ffe5a3'}),scene,8);}
box(83,.005,-760,18,.05,1250,'#767c70',scene);box(45,.009,-320,83,.07,18,'#73786f',scene);
for(let i=0;i<7;i++){const z=-220-i*110;box(180,6,z,65,12,65,'#a9aca0',scene);const roof=box(180,12,z,69,1.2,70,'#6d7a78',scene);for(let j=0;j<3;j++)box(147,4,z-20+j*20,.2,7,15,'#546465',scene);}
box(135,13,-130,10,26,10,'#b5b8ac',scene);box(135,27,-130,17,5,17,'#405d68',scene);box(135,30,-130,19,1,19,'#7b8788',scene);
for(let i=0;i<90;i++){const x=(rand()-.5)*6500,z=-2800-rand()*5000;const height=150+rand()*550;const m=mesh(new T.ConeGeometry(250+rand()*400,height,5),mat(['#8c9a8e','#839489','#98a399'][i%3]),scene);m.position.set(x,height/2-70,z);m.rotation.y=rand()*6;}
const treeGeo=new T.ConeGeometry(4,17,6),treeMat=mat('#344e3d');for(let i=0;i<180;i++){let x=80+rand()*1000;if(i%2)x=-100-rand()*1100;const z=400-rand()*3800;const m=mesh(treeGeo,treeMat,scene);m.position.set(x,7,z);m.scale.setScalar(.7+rand()*.9);}
const sunDisc=ell(-2900,1500,-6500,180,180,180,new T.MeshBasicMaterial({color:'#ffe9b9'}),scene,24);

// Light-aircraft cabin and the actual exterior used by the landing replay.
const navy=mat('#172a32',.65,.1),rim=mat('#53616a',.45,.3),trim=mat('#c5b99e',.7),leather=mat('#4c3e32',.9);
box(0,.42,.5,2.05,.14,3.8,navy);box(-1.01,.95,.65,.12,1.05,2.8,navy);box(1.01,.95,.65,.12,1.05,2.8,navy);
for(let x of [-1.0,1.0]){link([x,1.13,-.82],[x*.84,2.13,-.48],.055,rim);link([x*.84,2.13,-.48],[x,2.15,1.8],.045,rim);link([x,1.2,1.85],[x,2.15,1.8],.05,rim);link([x,1.22,-.84],[x,1.2,1.9],.045,trim);}
link([-.84,2.13,-.48],[.84,2.13,-.48],.055,rim);link([0,1.13,-.86],[0,2.13,-.51],.035,rim);
box(0,1.0,-.55,1.99,.47,.4,navy);box(0,1.245,-.67,2.04,.08,.62,mat('#101b21'));
for(let x of [-.47,.48]){box(x,.7,1.1,.68,.18,.72,leather);const seat=box(x,1.08,1.42,.67,.8,.15,leather);seat.rotation.x=-.12;box(x,1.5,1.46,.43,.23,.16,leather);}
box(.05,.7,.36,.19,.29,1.05,navy);
const gauges=[];
for(let i=0;i<6;i++){
 const x=-.72+(i%3)*.25,y=1.09-Math.floor(i/3)*.22;
 const ring=mesh(new T.CylinderGeometry(.103,.103,.02,40),mat('#080e13',.35,.2));ring.rotation.x=Math.PI/2;ring.position.set(x,y,-.326);
 const canvas=document.createElement('canvas');canvas.width=192;canvas.height=192;const texture=new T.CanvasTexture(canvas);texture.colorSpace=T.SRGBColorSpace;
 const face=mesh(new T.CircleGeometry(.094,40),new T.MeshBasicMaterial({map:texture}));face.position.set(x,y,-.311);gauges.push({canvas,texture,index:i});
}
planeLabel('COM  118.700',.46,1.115,-.32,.56,.09);planeLabel('NAV  110.30',.46,.985,-.32,.56,.09);planeLabel('FLY-BY-FLY',.48,.845,-.32,.5,.055);
for(let i=0;i<7;i++)ell(.16+i*.09,.735,-.312,.019,.019,.022,i%3===0?'#c65d36':'#b2b5a6');
const throttle=link([.05,.84,.12],[.05,1.03,-.04],.018,rim);const throttleCap=ell(.05,1.03,-.04,.044,.034,.034,'#ba4634');
const yoke=new T.Group();yoke.position.set(-.46,1.05,.04);aircraft.add(yoke);link([0,0,.04],[0,0,-.33],.025,rim,yoke);link([-.2,.08,0],[0,-.055,0],.025,navy,yoke);link([0,-.055,0],[.2,.08,0],.025,navy,yoke);link([-.2,.08,0],[-.2,.2,0],.034,navy,yoke);link([.2,.08,0],[.2,.2,0],.034,navy,yoke);ell(0,-.04,.035,.055,.035,.019,'#be9a54',yoke);
const exterior=new T.Group();aircraft.add(exterior);
ell(0,.69,1.3,.98,.66,2.3,'#d9d5bf',exterior);ell(0,.74,-1.48,.81,.58,1.1,'#dad7c5',exterior);box(0,.3,.9,10.8,.12,1.5,'#d7d4bd',exterior);box(0,.68,4.0,3.6,.10,.75,'#d7d4bd',exterior);box(0,1.12,4.1,.12,1.25,.75,'#384d50',exterior);
for(let x of [-1.1,1.1]){link([x*.5,.4,.6],[x,-.5,.6],.047,rim,exterior);const tire=mesh(new T.CylinderGeometry(.24,.24,.16,20),mat('#161c1d'),exterior);tire.rotation.z=Math.PI/2;tire.position.set(x,-.5,.6);}
link([0,.3,-1.5],[0,-.5,-1.5],.045,rim,exterior);const noseTire=mesh(new T.CylinderGeometry(.19,.19,.14,20),mat('#161c1d'),exterior);noseTire.rotation.z=Math.PI/2;noseTire.position.set(0,-.5,-1.5);
const prop=new T.Group();prop.position.set(0,.76,-2.6);exterior.add(prop);box(0,0,0,.09,2.15,.03,'#17292f',prop);ell(0,0,-.05,.16,.16,.24,'#bfae86',prop);

// Procedural Drosophila: six segmented legs, compound eyes, antennae and wings.
const fly=new T.Group();fly.position.set(-.47,1.03,.75);aircraft.add(fly);
const shell=mat('#57472c',.58,.12),darkShell=mat('#2a2b21',.66,.1),legmat=mat('#625039',.6);
ell(0,.1,.1,.23,.24,.27,shell,fly);ell(0,-.02,.43,.22,.18,.34,shell,fly);
for(let i=0;i<5;i++){const ring=mesh(new T.TorusGeometry(.19-i*.017,.012,6,30),darkShell,fly);ring.rotation.x=Math.PI/2;ring.scale.x=1.03;ring.position.set(0,-.02,.27+i*.088);}
const head=new T.Group();head.position.set(0,.38,-.13);fly.add(head);ell(0,0,0,.21,.185,.17,shell,head);
for(let side of [-1,1]){
 ell(side*.165,.006,-.035,.13,.174,.147,mat('#812c16',.4,.05),head,32);
 const facetGeo=new T.SphereGeometry(1,5,4),facetMat=mat('#b74624',.38,.12),facets=new T.InstancedMesh(facetGeo,facetMat,190);head.add(facets);const dummy=new T.Object3D();let k=0;
 for(let row=0;row<14;row++){const theta=.18+row*Math.PI/14;for(let col=0;col<14;col++){if(k>=190)break;const az=-Math.PI+(col+(row%2)*.5)*Math.PI*2/14;dummy.position.set(side*.165+.132*Math.sin(theta)*Math.cos(az),.006+.175*Math.cos(theta),-.035+.149*Math.sin(theta)*Math.sin(az));dummy.scale.set(.013,.012,.012);dummy.updateMatrix();facets.setMatrixAt(k,dummy.matrix);facets.setColorAt(k,new T.Color().setHSL(.025+rand()*.015,.6,.18+rand()*.09));k++;}}
 facets.count=k;
 link([side*.065,.07,-.15],[side*.12,.17,-.23],.009,legmat,head);link([side*.12,.17,-.23],[side*.15,.22,-.27],.006,legmat,head);
 for(let i=0;i<4;i++)link([side*.13,.18+i*.01,-.24],[side*(.16+i*.014),.2+i*.02,-.27],.002,legmat,head);
}
ell(0,-.12,-.18,.028,.032,.06,'#9b7550',head);
// Headset follows the head; no human face is drawn onto the insect.
const band=mesh(new T.TorusGeometry(.238,.017,8,40,Math.PI),mat('#17252c',.3,.3),head);band.position.y=.015;
for(let side of [-1,1])ell(side*.235,.02,.025,.045,.083,.055,'#1d2c32',head);
link([-.23,.015,-.02],[-.22,-.12,-.17],.009,'#1a272c',head);link([-.22,-.12,-.17],[-.06,-.13,-.23],.008,'#1a272c',head);ell(-.05,-.13,-.23,.027,.014,.015,'#121b20',head);
const cap=ell(0,.155,.012,.17,.052,.13,'#1b2e39',head);box(0,.137,-.13,.23,.012,.13,'#1b2e39',head);link([-.13,.14,-.1],[.13,.14,-.1],.006,'#d4ae62',head);
const wingMat=new T.MeshPhysicalMaterial({color:'#dbe9e3',transparent:true,opacity:.35,roughness:.3,metalness:.1,side:T.DoubleSide,depthWrite:false});
for(let side of [-1,1]){
 const shape=new T.Shape();shape.moveTo(0,0);shape.bezierCurveTo(.08,.04,.32,.2,.42,.65);shape.bezierCurveTo(.48,.9,.1,1.08,-.02,.73);shape.bezierCurveTo(-.12,.4,-.04,.08,0,0);
 const wing=mesh(new T.ShapeGeometry(shape,16),wingMat,fly);wing.rotation.x=Math.PI/2;wing.rotation.z=side*.32;wing.scale.x=side*.85;wing.position.set(side*.11,.27,.1);
 for(let j=0;j<4;j++){const pts=[];for(let i=0;i<12;i++){const t=i/11;pts.push(new T.Vector3(side*(.1+.35*t+(j-1.5)*.045*t),.277-.03*t,.1+.81*t));}const vein=new T.Line(new T.BufferGeometry().setFromPoints(pts),new T.LineBasicMaterial({color:'#a6a889',transparent:true,opacity:.55}));fly.add(vein);}
}
const frontLegs=[];
for(let side of [-1,1])for(let pair=0;pair<3;pair++){
 const a=[side*.16,.09,.02+pair*.12];let b,c;
 if(pair===0){b=[side*.30,.01,-.25];c=[side*.21,.2,-.71];}
 else if(pair===1){b=[side*.34,-.17,.13];c=[side*.35,-.32,.38];}
 else{b=[side*.31,-.12,.56];c=[side*.28,-.33,.73];}
 const upper=link(a,b,.013,legmat,fly),lower=link(b,c,.009,legmat,fly);ell(...b,.02,.02,.02,legmat,fly,12);if(pair===0)frontLegs.push({side,a,b,c,upper,lower});
}
for(let i=0;i<42;i++){const theta=rand()*6.28,z=rand()*.42;const a=[Math.cos(theta)*.205,.1+Math.sin(theta)*.21,z];const b=[a[0]*1.12,a[1]+.03,z+.014];link(a,b,.0018,'#322c20',fly);}

function drawGauges(f){
 const values=[f.airspeed,f.phi*180/Math.PI,f.alt*3.28084,f.heading*180/Math.PI,f.vs*196.85,f.controls?.[2]||0];
 const names=['AIRSPEED','ATTITUDE','ALTITUDE','HEADING','VERT SPEED','POWER'];
 gauges.forEach(({canvas,texture,index:i})=>{const x=canvas.getContext('2d');x.clearRect(0,0,192,192);x.fillStyle='#101a20';x.beginPath();x.arc(96,96,95,0,7);x.fill();x.save();x.beginPath();x.arc(96,96,85,0,7);x.clip();
 if(i===1){x.translate(96,96);x.rotate(-f.phi);x.fillStyle='#5e9cb5';x.fillRect(-160,-200+f.theta*190,320,200);x.fillStyle='#987247';x.fillRect(-160,f.theta*190,320,220);x.strokeStyle='#e9e7d8';x.lineWidth=3;x.beginPath();x.moveTo(-100,f.theta*190);x.lineTo(100,f.theta*190);x.stroke();x.restore();x.strokeStyle='#e5b85a';x.lineWidth=4;x.beginPath();x.moveTo(48,96);x.lineTo(83,96);x.lineTo(96,103);x.lineTo(109,96);x.lineTo(144,96);x.stroke();}
 else{x.restore();for(let t=0;t<40;t++){const a=t/40*Math.PI*2;x.strokeStyle=t%5===0?'#d5dfd9':'#687b7d';x.lineWidth=t%5===0?2:1;x.beginPath();x.moveTo(96+Math.sin(a)*74,96-Math.cos(a)*74);x.lineTo(96+Math.sin(a)*(t%5===0?64:69),96-Math.cos(a)*(t%5===0?64:69));x.stroke();}let a=i===0?(values[i]-40)/120*5-2.5:i===2?values[i]/1000*6.28:i===3?values[i]*Math.PI/180:i===4?values[i]/2000*2.5:values[i]*4-2;x.strokeStyle='#edeee0';x.lineWidth=3;x.beginPath();x.moveTo(96-Math.sin(a)*12,96+Math.cos(a)*12);x.lineTo(96+Math.sin(a)*62,96-Math.cos(a)*62);x.stroke();x.fillStyle='#d9e3de';x.font='bold 13px monospace';x.textAlign='center';x.fillText(Math.round(values[i]*(i===5?100:1)),96,137);}
 x.fillStyle='#c6d3cf';x.font='9px Arial';x.textAlign='center';x.fillText(names[i],96,53);texture.needsUpdate=true;
 });
}

const bc=document.getElementById('brain-canvas'),bx=bc.getContext('2d');const brainDots=[];
for(let i=0;i<384;i++){const side=i<192?-1:1,u=(i%192)/192,ang=i*2.399963;const r=Math.sqrt(u);brainDots.push([300+side*105+Math.cos(ang)*r*105,112+Math.sin(ang)*r*76]);}
function drawBrain(f){bx.clearRect(0,0,600,240);const activity=f.neural?.sample||[];for(let i=0;i<384;i++){const value=activity[i]||0,v=Math.min(1,Math.abs(value)*8);bx.fillStyle=value>=0?`rgba(113,225,210,${.12+.88*v})`:`rgba(230,191,123,${.12+.88*v})`;bx.beginPath();bx.arc(...brainDots[i],1.3+v*1.8,0,7);bx.fill();}bx.fillStyle='#8babae';bx.font='14px monospace';bx.textAlign='center';bx.fillText('384 SAMPLED RATES / SCHEMATIC LAYOUT',300,226);}

const frames=D.frames;const total=frames[frames.length-1].t;let view='auto',playing=!capture,t=0,previous=performance.now();
const playback=D.playback_rate||1;const clipDuration=total/playback;
function at(time){let lo=0,hi=frames.length-1;while(lo<hi){const m=(lo+hi+1)>>1;if(frames[m].t<=time)lo=m;else hi=m-1;}const a=frames[lo],b=frames[Math.min(lo+1,frames.length-1)],q=b.t===a.t?0:(time-a.t)/(b.t-a.t);const out={...a};for(const k of ['north','east','alt','phi','theta','heading','airspeed','vs'])out[k]=a[k]+(b[k]-a[k])*q;out.controls=a.controls.map((v,i)=>v+(b.controls[i]-v)*q);return out;}
const pos=new T.Vector3(),target=new T.Vector3();
function localCamera(cam,p,look){cam.position.copy(aircraft.localToWorld(new T.Vector3(...p)));cam.up.set(0,1,0).applyQuaternion(aircraft.quaternion);cam.lookAt(aircraft.localToWorld(new T.Vector3(...look)));}
function render(clipTime){
 t=Math.max(0,Math.min(clipDuration,clipTime));const f=at(t*playback);
 const visualOffset=D.result?.cg_height != null ? .74 - D.result.cg_height : 0;
 aircraft.position.set(f.east,f.alt+visualOffset,-f.north);aircraft.rotation.set(f.theta,-f.heading,-f.phi,'YXZ');
 // Stylized tires differ from JSBSim gear geometry. After physical contact,
 // keep the displayed tires above the runway; never alter physics or telemetry.
 if(D.touchdown_time!=null && t*playback>=D.touchdown_time){
  const axisX=new T.Vector3(1,0,0).applyQuaternion(aircraft.quaternion);
  const axisY=new T.Vector3(0,1,0).applyQuaternion(aircraft.quaternion);
  const axisZ=new T.Vector3(0,0,1).applyQuaternion(aircraft.quaternion);
  let bottom=Infinity;
  for(const [x,z,r,w] of [[-1.1,.6,.24,.08],[1.1,.6,.24,.08],[0,-1.5,.19,.07]]){
   const center=new T.Vector3(x,-.5,z).applyQuaternion(aircraft.quaternion);
   bottom=Math.min(bottom,center.y-r*Math.hypot(axisY.y,axisZ.y)-w*Math.abs(axisX.y));
  }
  aircraft.position.y=Math.max(aircraft.position.y,.035-bottom);
 }
 sun.position.copy(aircraft.position).add(new T.Vector3(-200,300,-500));sun.target.position.copy(aircraft.position);
 yoke.rotation.z=-f.controls[0]*.65;yoke.position.z=.04+f.controls[1]*.10;
 head.rotation.y=Math.sin(t*.9)*.045;head.rotation.x=-f.controls[1]*.035;prop.rotation.z=t*80;
 frontLegs.forEach(l=>{const a=f.controls[0]*.45,c=[l.side*.2*Math.cos(a),.2+l.side*.2*Math.sin(a),-.71+f.controls[1]*.10];setLink(l.lower,l.b,c);});
 let chosen=view;
 const touchdown=D.touchdown_time==null?total:D.touchdown_time;
 if(chosen==='auto')chosen=t<4.0?'pilot':t*playback>touchdown-3?'chase':'cockpit';
 if(chosen==='pilot'){localCamera(camera,[.61,1.67,-.44],[-.45,1.36,.67]);camera.fov=57;exterior.visible=false;}
 else if(chosen==='cockpit'){localCamera(camera,[.36,1.78,1.83],[-.12,1.40,-4]);camera.fov=61;exterior.visible=false;}
 else {camera.up.set(0,1,0);camera.position.set(f.east+18,f.alt+7,-f.north+24);target.set(f.east,f.alt+.6,-f.north-4);camera.lookAt(target);camera.fov=48;exterior.visible=true;}
 camera.updateProjectionMatrix();drawGauges(f);renderer.render(scene,camera);
 exterior.visible=false;localCamera(pilotCamera,[.15,1.65,-.37],[-.46,1.34,.68]);pilotRenderer.render(scene,pilotCamera);
 drawBrain(f);
 document.getElementById('hook').style.opacity=t<4?1:0;document.getElementById('status').style.opacity=t>=4?1:0;
 const landed=D.touchdown_time!=null&&t*playback>=touchdown;document.getElementById('phase').textContent=landed?'TOUCHDOWN':f.alt<12?'SHORT FINAL':'FINAL APPROACH';
 document.getElementById('speed').textContent=Math.round(f.airspeed);document.getElementById('altitude').textContent=Math.max(0,Math.round(f.alt*3.28084));document.getElementById('vs').textContent=(f.vs>0?'+':'')+Math.round(f.vs*196.85/10)*10;
 document.getElementById('distance').textContent=Math.max(0,Math.round(-f.north))+' M';
 document.getElementById('roll-bar').style.left=(50+f.controls[0]*45)+'%';document.getElementById('pitch-bar').style.left=(50+f.controls[1]*45)+'%';
 document.getElementById('neurons').textContent=D.preview?'NOT CONNECTED':(D.neurons||0).toLocaleString()+' NEURONS';
 document.getElementById('clock').textContent=`${String(Math.floor(t/60)).padStart(2,'0')}:${String(Math.floor(t%60)).padStart(2,'0')}  /  ${playback}× REPLAY`;
 let radio=t<4?'Your pilot today has never seen an airplane.':t<9?'Drosophila One, cleared to land.':t<14?'Maintain runway heading.':t*playback<touchdown-4?'Looking good, Drosophila One.':'Welcome to the ground, Captain.';
 document.getElementById('radio-text').textContent=radio;document.querySelector('#radio>span').textContent=t<4?'CABIN':'TOWER';
 const finished=t*playback>touchdown+2&&D.landed;document.getElementById('result').style.opacity=finished?1:0;
 document.getElementById('result-title').textContent=D.landed?'The fly landed the plane.':'We will be reviewing this.';
 const r=D.result||{};document.getElementById('result-detail').textContent=`TOUCHDOWN  ${Math.round((r.sink_rate||0)*196.85)} FT/MIN\nCENTERLINE ERROR  ${Math.abs(r.lateral_error||0).toFixed(1)} M`;
 document.getElementById('radio').style.opacity=finished?0:1;
 document.getElementById('seek').value=Math.round(t/clipDuration*1000);
 window.__frame=f;
}
window.seekTime=render;window.clipDuration=clipDuration;window.setCamera=v=>{view=v;render(t);};window.__ready=true;
if(D.preview){document.getElementById('disclosure').textContent='SCENE PREVIEW — illustrative aircraft pose; neural controller not connected';document.getElementById('mode').textContent='LAYOUT PREVIEW';document.querySelector('#hook p').textContent='Cockpit artwork preview. Flight/controller validation is next.';}
document.querySelectorAll('[data-camera]').forEach(b=>b.onclick=()=>{view=b.dataset.camera;render(t);});
document.getElementById('play').onclick=()=>{playing=!playing;document.getElementById('play').textContent=playing?'Pause':'Play';};
document.getElementById('restart').onclick=()=>{t=0;playing=true;};document.getElementById('seek').oninput=e=>{playing=false;render(e.target.value/1000*clipDuration);};
function resize(){const app=document.getElementById('app');if(innerWidth<900){app.style.transform=`scale(${Math.min(innerWidth/1280,innerHeight/720)})`;}else{app.style.transform='';renderer.setSize(innerWidth,innerHeight,false);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();}}
addEventListener('resize',resize);resize();render(0);
function animate(now){const dt=Math.min(.1,(now-previous)/1000);previous=now;if(playing){t+=dt;if(t>clipDuration)t=0;render(t);}requestAnimationFrame(animate);}requestAnimationFrame(animate);
})();
