// Native WebGL2: actual indexed surfaces, world-space lighting and a scroll-driven camera.
// All geometry, shaders and environment lighting are original procedural code. No textures or network calls.
const TAU=Math.PI*2;
export const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
export const smooth=(a,b,x)=>{const t=clamp((x-a)/(b-a));return t*t*(3-2*t);};
const mix=(a,b,t)=>a+(b-a)*t;
const norm=v=>{const l=Math.hypot(...v)||1;return v.map(x=>x/l);};
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
export function torus(segments=96,sides=20,arc=TAU,tube=.14){
  const positions=[],normals=[],indices=[];
  for(let i=0;i<=segments;i++){const a=i/segments*arc;for(let j=0;j<=sides;j++){const b=j/sides*TAU;positions.push((1+tube*Math.cos(b))*Math.cos(a),(1+tube*Math.cos(b))*Math.sin(a),tube*Math.sin(b));normals.push(Math.cos(b)*Math.cos(a),Math.cos(b)*Math.sin(a),Math.sin(b));}}
  for(let i=0;i<segments;i++)for(let j=0;j<sides;j++){const k=i*(sides+1)+j;indices.push(k,k+sides+1,k+1,k+1,k+sides+1,k+sides+2);}
  return{positions,normals,indices};
}
export function bevelBox(){
  const positions=[],normals=[],indices=[],n=4,r=.17;
  for(const [normal,u,v] of [[[1,0,0],[0,0,-1],[0,1,0]],[[-1,0,0],[0,0,1],[0,1,0]],[[0,1,0],[1,0,0],[0,0,-1]],[[0,-1,0],[1,0,0],[0,0,1]],[[0,0,1],[1,0,0],[0,1,0]],[[0,0,-1],[-1,0,0],[0,1,0]]]){
    const start=positions.length/3;
    for(let y=0;y<=n;y++)for(let x=0;x<=n;x++){const p=normal.map((k,i)=>k+u[i]*(x/n*2-1)+v[i]*(y/n*2-1));const c=p.map(k=>clamp(k,-1+r,1-r));const q=norm(p.map((k,i)=>k-c[i]));positions.push(...c.map((k,i)=>k+q[i]*r));normals.push(...q);}
    for(let y=0;y<n;y++)for(let x=0;x<n;x++){const k=start+y*(n+1)+x;indices.push(k,k+1,k+n+1,k+1,k+n+2,k+n+1);}
  }return{positions,normals,indices};
}
export function transform(position=[0,0,0],rotation=[0,0,0],scale=[1,1,1]){
  const [x,y,z]=rotation,[a,b,c]=[Math.cos(x),Math.cos(y),Math.cos(z)],[d,e,f]=[Math.sin(x),Math.sin(y),Math.sin(z)];
  const r=[b*c,b*f,-e,d*e*c-a*f,d*e*f+a*c,d*b,a*e*c+d*f,a*e*f-d*c,a*b];
  return{model:new Float32Array([r[0]*scale[0],r[1]*scale[0],r[2]*scale[0],0,r[3]*scale[1],r[4]*scale[1],r[5]*scale[1],0,r[6]*scale[2],r[7]*scale[2],r[8]*scale[2],0,...position,1]),normal:new Float32Array(r.map((v,i)=>v/scale[Math.floor(i/3)]))};
}
const vertex=`#version 300 es
precision highp float;
layout(location=0) in vec3 position;layout(location=1) in vec3 normal;
uniform mat4 model,view,projection;uniform mat3 normalMatrix;
out vec3 world;out vec3 N;
void main(){vec4 p=model*vec4(position,1.);world=p.xyz;N=normalize(normalMatrix*normal);gl_Position=projection*view*p;}`;
const fragment=`#version 300 es
precision highp float;
in vec3 world;in vec3 N;out vec4 color;
uniform vec3 eye,base;uniform vec4 material;uniform float lightShift;
vec3 lamp(vec3 n,vec3 v,vec3 l,vec3 tint){vec3 h=normalize(l+v);float nl=max(dot(n,l),0.);float nv=max(dot(n,v),.001);float nh=max(dot(n,h),0.);float vh=max(dot(v,h),0.);float a=max(.025,material.x*material.x);float d=a*a/(3.14159*pow(nh*nh*(a*a-1.)+1.,2.));float k=pow(material.x+1.,2.)/8.;float g=(nv/(nv*(1.-k)+k))*(nl/(nl*(1.-k)+k));vec3 f0=mix(vec3(.05),base,material.y);vec3 f=f0+(1.-f0)*pow(1.-vh,5.);return((1.-material.y)*base*.4+f*d*g/max(.004,4.*nv*nl))*tint*nl;}
void main(){vec3 n=normalize(N);if(!gl_FrontFacing)n=-n;vec3 v=normalize(eye-world);vec3 r=reflect(-v,n);float fres=pow(1.-max(dot(n,v),0.),3.);vec3 env=mix(vec3(.09,.13,.19),vec3(.92,1.05,1.16),pow(r.y*.5+.5,2.));env+=vec3(1.,.88,.66)*pow(max(0.,dot(r,normalize(vec3(-.6,.8,1.)))),50.)*2.8;env+=vec3(.48,.62,.95)*pow(max(0.,dot(r,normalize(vec3(.8,.2,.5)))),28.)*1.2;vec3 sheen=.5+.5*cos(vec3(0.,2.,4.)+fres*7.+n.y*2.);vec3 c=base*.08+env*mix(.35,.95,material.y)+sheen*fres*.2;c+=lamp(n,v,normalize(vec3(-3.+lightShift,5.,4.)-world),vec3(1.3,1.12,.91));c+=lamp(n,v,normalize(vec3(4.,2.,-3.)-world),vec3(.45,.7,1.1));c+=base*material.z;float fog=1.-exp(-length(eye-world)*.022);c=mix(c,vec3(.035,.07,.105),fog);c=c/(1.+c);color=vec4(pow(c,vec3(.82)),material.w);}`;
const bgVertex=`#version 300 es
const vec2 p[3]=vec2[3](vec2(-1.,-1.),vec2(3.,-1.),vec2(-1.,3.));out vec2 uv;void main(){uv=p[gl_VertexID]*.5+.5;gl_Position=vec4(p[gl_VertexID],.999,1.);}`;
const bgFragment=`#version 300 es
precision highp float;in vec2 uv;out vec4 color;uniform float phase;
void main(){vec2 p=(uv-vec2(.65,.5))*vec2(1.5,1.);float glow=exp(-dot(p,p)*3.2);float beam=exp(-pow((uv.x-.73)+(uv.y-.5)*.25,2.)*70.);vec3 c=mix(vec3(.023,.043,.067),vec3(.075,.16,.205),glow);c+=vec3(.1,.065,.14)*beam*.2;c+=vec3(.015,.035,.04)*phase;color=vec4(c,1.);}`;
function program(gl,vs,fs){const objects=[];try{const shaders=[vs,fs].map((source,i)=>{const shader=gl.createShader(i?gl.FRAGMENT_SHADER:gl.VERTEX_SHADER);objects.push(shader);gl.shaderSource(shader,source);gl.compileShader(shader);if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw Error('Portal shader compilation failed');return shader;});const p=gl.createProgram();shaders.forEach(s=>gl.attachShader(p,s));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS)){gl.deleteProgram(p);throw Error('Portal shader linking failed');}return p;}finally{objects.forEach(s=>gl.deleteShader(s));}}
export function createEventPortalRenderer(canvas,{compact=false}={}){
  const gl=canvas.getContext('webgl2',{alpha:false,antialias:!compact,powerPreference:'low-power',preserveDrawingBuffer:true});
  if(!gl)throw Error('WebGL2 unavailable');
  const resources=[],main=program(gl,vertex,fragment),back=program(gl,bgVertex,bgFragment);
  function mesh(data){const vao=gl.createVertexArray();gl.bindVertexArray(vao);resources.push(['vao',vao]);for(const [location,values] of [[0,data.positions],[1,data.normals]]){const buffer=gl.createBuffer();resources.push(['buffer',buffer]);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(values),gl.STATIC_DRAW);gl.enableVertexAttribArray(location);gl.vertexAttribPointer(location,3,gl.FLOAT,false,0,0);}const index=gl.createBuffer();resources.push(['buffer',index]);gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,index);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array(data.indices),gl.STATIC_DRAW);return{vao,count:data.indices.length};}
  const ring=mesh(torus(compact?56:112,compact?12:24)),arc=mesh(torus(compact?40:80,compact?12:20,Math.PI*1.5,.1)),box=mesh(bevelBox());
  const U=Object.fromEntries(['model','view','projection','normalMatrix','eye','base','material','lightShift'].map(n=>[n,gl.getUniformLocation(main,n)]));
  const phase=gl.getUniformLocation(back,'phase');let dead=false,draws=0;
  function draw(shape,pos,rot,scale,base,material){const t=transform(pos,rot,scale);gl.uniformMatrix4fv(U.model,false,t.model);gl.uniformMatrix3fv(U.normalMatrix,false,t.normal);gl.uniform3fv(U.base,base);gl.uniform4fv(U.material,material);gl.bindVertexArray(shape.vao);gl.depthMask(material[3]>=1);gl.drawElements(gl.TRIANGLES,shape.count,gl.UNSIGNED_SHORT,0);gl.depthMask(true);draws++;}
  function render(progress,point,width,height){
    if(dead||gl.isContextLost()||width<1||height<1)return;
    const p=clamp(progress),mobile=width<650,dpr=Math.min(devicePixelRatio||1,compact?1:1.3,Math.sqrt((compact?500000:1100000)/(width*height))),w=Math.max(1,Math.round(width*dpr)),h=Math.max(1,Math.round(height*dpr));
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}gl.viewport(0,0,w,h);gl.clearColor(.025,.05,.08,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.disable(gl.DEPTH_TEST);gl.disable(gl.BLEND);gl.useProgram(back);gl.bindVertexArray(null);gl.uniform1f(phase,p);gl.drawArrays(gl.TRIANGLES,0,3);gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);gl.cullFace(gl.BACK);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.useProgram(main);
    const travel=smooth(.08,.91,p),eye=[point.x*.22, .45+point.y*.12,mix(mobile?11:8.3,-4.0,travel)],target=[0,.05,eye[2]-6];
    const z=norm(eye.map((n,i)=>n-target[i])),x=norm(cross([0,1,0],z)),y=cross(z,x);
    const view=new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1]);
    const f=1/Math.tan(38*Math.PI/360),a=w/h,near=.08,far=60,projection=new Float32Array([f/a,0,0,0,0,f,0,0,mobile?0:mix(-.34,-.25,travel),mobile?-.08:0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0]);
    gl.uniformMatrix4fv(U.view,false,view);gl.uniformMatrix4fv(U.projection,false,projection);gl.uniform3fv(U.eye,eye);gl.uniform1f(U.lightShift,point.x*.8);draws=0;
    const open=smooth(.18,.65,p),gold=[.94,.71,.4],silver=[.62,.72,.8],violet=[.56,.47,.74],dark=[.09,.16,.2];
    // Four heavy, independently separating metal/glass optical layers. True depth, not DOM transforms.
    draw(ring,[0,0,0],[.12,-.3+open*.3+point.x*.035,.12+open*.18],[1.65,1.9,.88],gold,[.23,.92,0,1]);
    draw(arc,[0,0,-.18-open*.8],[-.06,.23-open*.42,-.28+open*.65],[1.42,1.66,1.1],silver,[.2,.88,0,1]);
    draw(ring,[0,0,-.5-open*1.1],[0,-.13+open*.32,.12-open*.25],[1.12,1.36,.58],violet,[.2,.7,.08,1]);
    const assemble=smooth(.52,.96,p),count=compact?8:12;
    // The inner world: scattered architectural ribs converge into a single ordered pavilion.
    for(let i=0;i<count;i++){
      const angle=i/count*TAU,chaos=1-assemble,px=Math.cos(angle)*2.15,pz=-11.6+Math.sin(angle)*1.45;
      const pos=[px+Math.sin(i*4.13)*chaos*2.8,-.32+Math.cos(i*2.7)*chaos*1.8,pz+Math.cos(i*1.9)*chaos*1.7];
      draw(box,pos,[chaos*Math.sin(i)*.65,angle+chaos*.8,chaos*Math.cos(i)*.6],[.13,mix(.38,1.15,assemble),.29],i%3?silver:gold,[.27,.82,0,1]);
    }
    draw(ring,[0,-1.55,-11.6],[Math.PI/2,0,0],[2.8,2.8,.16],dark,[.4,.75,0,1]);
    draw(arc,[0,1.05,-11.6],[Math.PI/2,0,mix(-.5,.15,assemble)],[2.24,2.24,.16],gold,[.23,.9,0,1]);
    draw(ring,[0,-1.38,-11.6],[Math.PI/2,0,0],[1.72,1.72,.05],[.3,.72,.79],[.3,.4,.85,.85]);
    // A rising, dimensional milestone path joins the composition. No stars, particle field or UI cards.
    for(let i=0;i<(compact?5:8);i++){const t=i/7,ax=-1.9+t*3.8,ay=-.65+Math.sin(t*Math.PI)*.75;
      draw(box,[ax+(1-assemble)*Math.sin(i*2)*1.1,ay,-11.6+Math.cos(t*Math.PI)*.9],[.1,Math.PI/4+(1-assemble)*i*.3,.12],[.085,.085,.085],silver,[.2,.7,.16,1]);
      if(i)draw(box,[ax-.26,ay-.05,-11.6+Math.cos(t*Math.PI)*.9],[0,.1,.24],[.2,.012,.012],[.4,.77,.82],[.4,.3,1.3,.8]);
    }
    // Transparent optical shell is composited after opaque world geometry without writing depth.
    draw(ring,[0,0,.15+open*.35],[.03,.1+open*.12,.06],[1.88,2.14,.24],silver,[.15,.65,.02,.42]);
    gl.bindVertexArray(null);return{cameraZ:eye[2],draws,triangles:ring.count/3};
  }
  function dispose(){if(dead)return;dead=true;for(const [kind,value] of resources){if(kind==='vao')gl.deleteVertexArray(value);else gl.deleteBuffer(value);}gl.deleteProgram(main);gl.deleteProgram(back);}
  return{render,dispose};
}
