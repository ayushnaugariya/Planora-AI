import assert from 'node:assert/strict';
import {torus,bevelBox,transform,smooth} from '../../frontend/modules/event-portal-renderer.js';

for(const mesh of [torus(),torus(56,12),torus(32,8,Math.PI*1.5),bevelBox()]){
  assert.equal(mesh.positions.length,mesh.normals.length);
  assert(mesh.positions.every(Number.isFinite)&&mesh.normals.every(Number.isFinite));
  assert.equal(mesh.indices.length%3,0);
  assert(mesh.indices.every(n=>Number.isInteger(n)&&n>=0&&n<mesh.positions.length/3&&n<65536));
  for(let i=0;i<mesh.normals.length;i+=3)assert(Math.abs(Math.hypot(...mesh.normals.slice(i,i+3))-1)<1e-6);
  const triangles=new Set();for(let i=0;i<mesh.indices.length;i+=3)triangles.add(mesh.indices.slice(i,i+3).sort((a,b)=>a-b).join(','));assert.equal(triangles.size,mesh.indices.length/3);
}
assert(torus(56,12).indices.length<torus().indices.length);
const result=transform([4,-2,8],[.3,-.8,.4],[2,3,.5]);
assert.equal(result.model.length,16);assert.equal(result.normal.length,9);assert([...result.model,...result.normal].every(Number.isFinite));assert.deepEqual([...result.model.slice(12)],[4,-2,8,1]);
assert.equal(smooth(.2,.8,-1),0);assert.equal(smooth(.2,.8,2),1);assert(smooth(.2,.8,.5)>.49&&smooth(.2,.8,.5)<.51);
console.log('PASS portal mesh topology, unit normals, 16-bit indices, compact geometry and bounded camera interpolation');
