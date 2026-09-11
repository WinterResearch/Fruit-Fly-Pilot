// Structural browser-code smoke test without a GPU. This does NOT replace
// visual inspection: WebGLRenderer is stubbed, Three's scene/math are real.
const fs=require('fs'),vm=require('vm'),path=require('path');
const root=__dirname;
const elements=new Map();
const context=new Proxy({}, {get(o,k){if(k in o)return o[k];return ()=>{};},set(o,k,v){o[k]=v;return true;}});
function element(id){if(!elements.has(id))elements.set(id,{style:{},classList:{add(){}},getContext(){return context;},textContent:'',value:0,hidden:true,width:192,height:192,addEventListener(){},setAttribute(){}});return elements.get(id);}
global.window=global;
global.document={getElementById:element,querySelector:element,querySelectorAll:()=>[],createElement:t=>({...element('new'+Math.random()),getContext:()=>context}),body:{classList:{add(){}}}};
global.location={search:'?capture=1'};global.innerWidth=1280;global.innerHeight=720;
global.addEventListener=()=>{};global.requestAnimationFrame=()=>{};
vm.runInThisContext(fs.readFileSync(path.join(root,'web/vendor/three.global.js'),'utf8'));
let renders=0,lastScene=null;
THREE.WebGLRenderer=class{constructor(){this.shadowMap={};}setPixelRatio(){}setSize(){}render(scene,camera){scene.updateMatrixWorld(true);camera.updateMatrixWorld(true);renders++;lastScene=scene;}};
vm.runInThisContext(fs.readFileSync(path.join(root,'web/replay.js'),'utf8'));
vm.runInThisContext(fs.readFileSync(path.join(root,'web/app.js'),'utf8'));
if(!global.__ready)throw Error('Scene did not become ready: '+element('error').textContent);
for(const t of [0,8,18,clipDuration-1])seekTime(t);
for(const camera of ['pilot','cockpit','chase'])setCamera(camera);
let meshes=0,triangles=0;lastScene.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3*(o.isInstancedMesh?o.count:1);}});
console.log(JSON.stringify({ready:global.__ready,renderCalls:renders,meshes,triangles,clipDuration,errors:element('error').textContent},null,2));
