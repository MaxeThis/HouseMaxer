// HouseMaxer room tracker engine
// -------------------------------------------------------------------------
// Turns Bluetooth distance readings (one per ESP32 scanner) into "where is
// the phone on my floor plan", without the dot jumping through walls.
//
//  - Each scanner has a learned radio map. For every 0.5 ft grid cell:
//      log10(reported_ft) = w0 + w1*log10(r) + w2*walls_crossed
//                           + w3 cos(th) + w4 sin(th) + w5 cos(2th) + w6 sin(2th)
//    r = 3D distance from scanner (x, y, z_m) to a phone at ENG.pz_m over
//    that cell, th = bearing on the plan. The w's come from
//    tracking/fit_radio_map.py (a calibration you record once).
//  - Belief lives on the grid. Between readings it spreads only through open
//    floor and doorways, never through walls.
//  - A Student-t likelihood shrugs off one blocked or spiky reading.
//  - The shown dot walks along open floor toward the estimate, with a
//    dead-band so it does not jitter.
//
// Floor-plan units are feet, origin top-left, y grows downward.
//
// Walls are a string of half-foot wall cells, ';'-separated:
//   'v<x>,<y0>'  a vertical wall piece at x, from y0 to y0+0.5
//   'h<y>,<x0>'  a horizontal wall piece at y, from x0 to x0+0.5
// Leave gaps for doorways. tracking/walls.py builds this string from boxes.
//
// Usage:
//   const eng = new MapEngine(CALIB, WALLS, {width_ft: 36, height_ft: 24});   // your plan's size
//   every second:  const cell = eng.step({scanner_key: distance_ft, ...});   // null if no readings
//                  if (cell != null) waypoints = eng.advance(cell);         // animate the dot along these
// -------------------------------------------------------------------------

// Example only: two rooms (12 x 10 ft each) joined by a 3 ft door. Replace
// with your own (tracking/walls.py) and your own fit (fit_radio_map.py).
export const EXAMPLE_WALLS = (() => {
  const out = [];
  for (let y = 0; y < 10; y += 0.5) if (y < 4 || y >= 7) out.push(`v12,${y}`);  // door from y=4 to y=7
  return out.join(';');
})();
export const EXAMPLE_CALIB = {
  fit: 'example',
  scanners: {
    ble_scanner_aaaaaa: {x: 2,  y: 5, w: [0.6, 0.55, 0.08, 0, 0, 0, 0], s: 0.2},
    ble_scanner_bbbbbb: {x: 22, y: 5, w: [0.6, 0.55, 0.08, 0, 0, 0, 0], s: 0.2},
    ble_scanner_cccccc: {x: 12, y: 0.5, w: [0.6, 0.55, 0.08, 0, 0, 0, 0], s: 0.2},
  },
};

// pz_m: phone height (m) the fit assumed; matches PHONE_Z_M in fit_radio_map.py
export const ENG = {pz_m:1.1, iters:20, alpha:0.24, eps:1e-3, infl:1.3, stale:5, R:12, dead:2.5, vmax:5.0};
export class MapEngine{
  // size: {width_ft, height_ft}. Grid is 0.5 ft.
  constructor(cal, walls, size){
    const NX=Math.round(size.width_ft*2), NY=Math.round(size.height_ft*2); this.NX=NX; this.NY=NY; this.N=NX*NY;
    this.cx=i=>(i+.5)*.5; this.cy=j=>(j+.5)*.5;
    const seg=[]; this.oE=new Uint8Array(NY*(NX-1)).fill(1); this.oS=new Uint8Array((NY-1)*NX).fill(1);
    walls.split(';').forEach(w=>{ const o=w[0]; const [c,s]=w.slice(1).split(',').map(Number);
      if(o==='v'){ seg.push([c,s,c,s+.5]); const i=Math.round(c/.5)-1, j=Math.round(s/.5); if(i>=0&&i<NX-1&&j>=0&&j<NY) this.oE[j*(NX-1)+i]=0; }
      else { seg.push([s,c,s+.5,c]); const j=Math.round(c/.5)-1, i=Math.round(s/.5); if(j>=0&&j<NY-1&&i>=0&&i<NX) this.oS[j*NX+i]=0; } });
    this.seg=seg; this.keys=Object.keys(cal.scanners); this.sc=cal.scanners; this.map={};
    for(const k of this.keys){ const S=cal.scanners[k], w=S.w, m=new Float32Array(this.N);
      for(let j=0;j<NY;j++) for(let i=0;i<NX;i++){ const x=this.cx(i), y=this.cy(j), dx=x-S.x, dy=y-S.y;
        const dz=S.z_m!=null?(S.z_m-ENG.pz_m)/0.3048:0, r=Math.max(Math.hypot(dx,dy,dz),1.0), th=Math.atan2(dy,dx), c=this.cross(S.x,S.y,x,y);
        m[j*NX+i]=w[0]+w[1]*Math.log10(r)+w[2]*c+w[3]*Math.cos(th)+w[4]*Math.sin(th)+w[5]*Math.cos(2*th)+w[6]*Math.sin(2*th); }
      this.map[k]=m; }
    this.reset();
  }
  reset(){ this.p=new Float64Array(this.N).fill(1/this.N); this.cell=null; this.ticks=0; }
  cross(ax,ay,bx,by){ let n=0; const dx=bx-ax, dy=by-ay;
    for(const [x1,y1,x2,y2] of this.seg){ const ex=x2-x1, ey=y2-y1, den=dx*ey-dy*ex; if(Math.abs(den)<1e-12) continue;
      const t=((x1-ax)*ey-(y1-ay)*ex)/den, u=((x1-ax)*dy-(y1-ay)*dx)/den; if(t>0&&t<1&&u>=0&&u<1) n++; } return n; }
  nbrs(c){ const NX=this.NX, j=(c/NX)|0, i=c%NX, out=[];
    if(i<NX-1&&this.oE[j*(NX-1)+i]) out.push(c+1); if(i>0&&this.oE[j*(NX-1)+i-1]) out.push(c-1);
    if(j<this.NY-1&&this.oS[j*NX+i]) out.push(c+NX); if(j>0&&this.oS[(j-1)*NX+i]) out.push(c-NX); return out; }
  diffuse(){ const NX=this.NX, NY=this.NY, a=ENG.alpha; let p=this.p; const f=new Float64Array(this.N);
    for(let it=0;it<ENG.iters;it++){ f.fill(0);
      for(let j=0;j<NY;j++) for(let i=0;i<NX-1;i++){ if(!this.oE[j*(NX-1)+i]) continue; const c=j*NX+i, d=p[c+1]-p[c]; f[c]+=d; f[c+1]-=d; }
      for(let j=0;j<NY-1;j++) for(let i=0;i<NX;i++){ if(!this.oS[j*NX+i]) continue; const c=j*NX+i, d=p[c+NX]-p[c]; f[c]+=d; f[c+NX]-=d; }
      for(let c=0;c<this.N;c++) p[c]+=a*f[c]; } }
  // readings: {scannerKey: distance_ft} (fresh ones only). returns target cell index
  step(readings){
    const N=this.N, e=ENG.eps; this.diffuse(); const p=this.p;
    for(let c=0;c<N;c++) p[c]=(1-e)*p[c]+e/N;
    const ll=new Float64Array(N); let used=0;
    for(const k of this.keys){ const v=readings[k]; if(!(v>0)) continue; used++;
      const y=Math.log10(v), m=this.map[k], s=this.sc[k].s*ENG.infl;
      for(let c=0;c<N;c++){ const r=(y-m[c])/s; ll[c]+=-2.5*Math.log1p(r*r/4); } }
    let mx=-Infinity; for(let c=0;c<N;c++){ ll[c]+=Math.log(p[c]+1e-300); if(ll[c]>mx) mx=ll[c]; }
    let sum=0, best=0; for(let c=0;c<N;c++){ p[c]=Math.exp(ll[c]-mx); sum+=p[c]; if(p[c]>p[best]) best=c; }
    for(let c=0;c<N;c++) p[c]/=sum;
    this.ticks++; this.used=used; if(!used) return null; return this.localTarget(best);
  }
  localTarget(c0){ const seen=new Map([[c0,0]]), q=[c0];
    for(let h=0;h<q.length;h++){ const c=q[h], d=seen.get(c); if(d>=ENG.R) continue;
      for(const n of this.nbrs(c)) if(!seen.has(n)){ seen.set(n,d+1); q.push(n); } }
    let sw=0,sx=0,sy=0; for(const c of seen.keys()){ const w=this.p[c]; sw+=w; sx+=w*this.cx(c%this.NX); sy+=w*this.cy((c/this.NX)|0); }
    sx/=sw; sy/=sw; let best=c0, bd=Infinity;
    for(const c of seen.keys()){ const d=(this.cx(c%this.NX)-sx)**2+(this.cy((c/this.NX)|0)-sy)**2; if(d<bd){bd=d;best=c;} }
    return best; }
  path(a,b){ if(a===b) return [a]; const prev=new Map([[a,-1]]), q=[a];
    for(let h=0;h<q.length;h++){ const c=q[h]; if(c===b) break; for(const n of this.nbrs(c)) if(!prev.has(n)){ prev.set(n,c); q.push(n); } }
    if(!prev.has(b)) return null; const out=[b]; while(out[out.length-1]!==a) out.push(prev.get(out[out.length-1])); return out.reverse(); }
  xy(c){ return {x:this.cx(c%this.NX), y:this.cy((c/this.NX)|0)}; }
  // advance the displayed position (cell) toward target along open floor; returns waypoint list for animation
  advance(target){
    if(this.cell==null){ this.cell=target; return [this.xy(target)]; }
    const a=this.xy(this.cell), b=this.xy(target);
    if(Math.hypot(b.x-a.x,b.y-a.y)<=ENG.dead) return [a];
    const pth=this.path(this.cell,target); if(!pth){ this.cell=target; return [b]; }
    const wp=[a]; let budget=ENG.vmax, cur=a;
    for(const c of pth.slice(1)){ const n=this.xy(c), d=Math.hypot(n.x-cur.x,n.y-cur.y); if(d>budget) break; budget-=d; cur=n; this.cell=c; wp.push(n); }
    return wp; }
}
