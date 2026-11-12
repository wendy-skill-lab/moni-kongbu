// ---------- app icons ----------
function appIcon(app,s=38){
 if(app==='car')return `<div style="width:${s}px;height:${s}px;border-radius:${s*0.23}px;background:linear-gradient(145deg,#30333b,#0b0c0f);display:flex;align-items:center;justify-content:center;box-shadow:inset 0 0 0 .5px rgba(255,255,255,.14)"><svg width="${s*0.64}" height="${s*0.64}" viewBox="0 0 24 24"><path d="M2.6 16c2.7-6 6-9 9.4-9s6.7 3 9.4 9" fill="none" stroke="${GOLD}" stroke-width="2.3" stroke-linecap="round"/><path d="M7.4 16c1.5-2.8 3-4.1 4.6-4.1s3.1 1.3 4.6 4.1" fill="none" stroke="${GOLD}" stroke-width="2.3" stroke-linecap="round"/></svg></div>`;
 return `<img src="${IC}wechat.png" style="width:${s}px;height:${s}px;border-radius:${s*0.23}px;display:block">`;
}
const GOLD='#d9b26f';
function carState(t){let s='drive';for(const x of F.car.state)if(t>=x[0])s=x[1];return s;}
function tapOn(what,t,w=0.22){return F.car.taps.some(x=>x.what===what&&t>=x.t-0.12&&t<x.t+w);}
const IRN=(t,op)=>`<img src="${A}noise/n${pad(Math.floor(t*15)%12)}.png" class="a" style="left:0;top:0;width:100%;height:100%;mix-blend-mode:overlay;opacity:${op}">`;
// ---------- 行云汽车 ----------
function carNav(title,sub){return `<div class="a" style="left:0;top:0;width:393px;height:98px;background:#0b0b0d"><div class="a" style="left:14px;top:65px">${G.back()}</div><div class="a cjk" style="left:0;width:393px;top:${sub?56:62}px;text-align:center;font:500 17px 'Noto Sans CJK SC';color:#efefef">${title}</div>${sub?`<div class="a cjk" style="left:0;width:393px;top:79px;text-align:center;font:400 11.5px 'InterV','Noto Sans CJK SC';color:#8b8b90">${sub}</div>`:''}<div class="a" style="right:18px;top:73px">${G.more}</div></div>`;}
function rangeAt(t){const L=F.sfx.locks;return t<L[1]?[386,78]:t<L[2]?[377,76]:t<L[3]?[371,75]:[357,72];}
function seatInfo(st){
 const occ=['未就座','1 人','#ff453a',1];
 if(st==='locked')return [['主驾','无人','#8b8b90',0],['后排右','无人','#8b8b90',0]];
 if(st==='parked')return [['主驾','无人','#8b8b90',0],['后排右','有人 · 车门已打开','#e8e8ec',0],occ];
 const r=[['主驾','有人 · 已系安全带','#e8e8ec',0],['后排右','有人 · 已系安全带','#e8e8ec',0]];
 if(st==='alert')r.push(occ);
 if(st==='alert2')r.push(['未就座','1 人 · 后排右','#ff453a',1]);
 return r;
}
function seatDiag(st,t,x,y){
 const pulse=0.5+0.5*Math.sin(t*6.2);
 const occ={drive:{d:1,rr:1},alert:{d:1,rr:1},alert2:{d:1,rr:1},parked:{rr:3},locked:{}}[st]||{};
 const seat=(sx,sy,w,h,k)=>{const v=occ[k]||0;const fill=v?'#e8e8ec':'none';const stroke=v?'#e8e8ec':'#4a4b52';
  return `<rect x="${sx}" y="${sy}" width="${w}" height="${h}" rx="5" fill="${fill}" stroke="${stroke}" stroke-width="1.4"/><rect x="${sx+3}" y="${sy-5}" width="${w-6}" height="5" rx="2" fill="${v?'#bdbdc2':'#3a3b41'}"/>`+(v===1?`<circle cx="${sx+w-2}" cy="${sy+h-2}" r="4.6" fill="#30d158" stroke="#16171a" stroke-width="1.6"/><path d="M${sx+w-4.3} ${sy+h-2.2}l1.6 1.6 3-3.2" stroke="#fff" stroke-width="1.3" fill="none"/>`:'');};
 const door=st==='parked'?`<path d="M105 90 L121 106" stroke="#ff9f0a" stroke-width="3.2" stroke-linecap="round"/>`:'';
 const blip=(cx,cy)=>`<circle cx="${cx}" cy="${cy}" r="${(5+6*pulse).toFixed(2)}" fill="none" stroke="#ff453a" stroke-width="1.5" opacity="${(0.15+0.8*(1-pulse)).toFixed(2)}"/><circle cx="${cx}" cy="${cy}" r="4.2" fill="#ff453a" stroke="#16171a" stroke-width="1.2"/>`;
 const b=st==='alert'?blip(63,132):(st==='alert2'||st==='parked')?blip(87,104):'';
 return `<svg class="a" style="left:${x}px;top:${y}px" width="126" height="150" viewBox="0 0 126 150"><rect x="21" y="3" width="84" height="144" rx="30" fill="#202227" stroke="#3a3c43" stroke-width="1.5"/><path d="M31 32 q32 -13 64 0" stroke="#4a4c53" stroke-width="1.5" fill="none"/><path d="M33 136 q30 7 60 0" stroke="#4a4c53" stroke-width="1.5" fill="none"/>${seat(31,46,27,28,'d')}${seat(68,46,27,28,'p')}${seat(29,96,20,28,'rl')}${seat(53,96,20,28,'rm')}${seat(77,96,20,28,'rr')}${door}${b}</svg>`;
}
function seatCard(st,t,y,h=158){
 const SI=seatInfo(st);const st0=SI.length>2?41:44,stp=SI.length>2?26:30;const rows=SI.map((r,i)=>`<div class="a cjk" style="left:16px;top:${st0+i*stp}px;font:400 13px 'Noto Sans CJK SC';color:#8b8b90;width:50px">${r[0]}</div><div class="a cjk" style="left:66px;top:${st0+i*stp}px;font:${r[3]?500:400} 13px 'Noto Sans CJK SC';color:${r[2]}">${r[1]}</div>`).join('');
 const warn=st==='alert'||st==='alert2'||st==='parked';
 const chip=warn?`<div class="a cjk" style="left:16px;top:${h-30}px;padding:2px 8px;border-radius:9px;background:rgba(255,69,58,.16);font:500 11.5px 'Noto Sans CJK SC';color:#ff6961">乘员感知 · 检测到未就座乘员</div>`:`<div class="a cjk" style="left:16px;top:${h-28}px;font:400 11.5px 'Noto Sans CJK SC';color:#6c6c72">${st==='locked'?'车辆已闭锁 · ':''}更新于 刚刚</div>`;
 return `<div class="a" style="left:12px;top:${y}px;width:369px;height:${h}px;border-radius:16px;background:#16171a"><div class="a cjk" style="left:16px;top:13px;font:500 15px 'Noto Sans CJK SC';color:#efefef">座椅与安全带</div>${rows}${chip}${seatDiag(st,t,232,(h-150)/2)}</div>`;
}
function carHome(t){
 const st=carState(t);const moving=st==='drive'||st==='alert'||st==='alert2';
 const spd=68+Math.floor(hash(Math.floor(t*1.2))*8);
 const chip=moving?`<span style="display:inline-block;width:7px;height:7px;border-radius:4px;background:#30d158;margin-right:6px;vertical-align:1px"></span>行驶中 · 代驾模式`:st==='locked'?`<span style="color:#9a9aa0">已闭锁</span>`:`<span style="color:#ff9f0a">右后门已打开</span>`;
 const qi=[['车锁',`<svg width="24" height="26" viewBox="0 0 24 26"><rect x="3.5" y="11" width="17" height="12.5" rx="2.5" fill="none" stroke="#e6e6e6" stroke-width="1.8"/><path d="M7.5 11V7.5a4.5 4.5 0 0 1 9 0V11" fill="none" stroke="#e6e6e6" stroke-width="1.8"/></svg>`],['车窗',`<svg width="28" height="24" viewBox="0 0 28 24"><path d="M3 20V9.5C3 6 5.5 4 9 4h16v16z" fill="none" stroke="#e6e6e6" stroke-width="1.8" stroke-linejoin="round"/><path d="M3 13h22" stroke="#e6e6e6" stroke-width="1.8"/></svg>`],['后备箱',`<svg width="30" height="24" viewBox="0 0 30 24"><path d="M3 15c0-4 3-7 8-8l9-1c4 .5 6 3 7 7" fill="none" stroke="#e6e6e6" stroke-width="1.8" stroke-linecap="round"/><path d="M3 15h24v3H3z" fill="none" stroke="#e6e6e6" stroke-width="1.8"/><circle cx="9" cy="19" r="2.6" fill="#0b0b0d" stroke="#e6e6e6" stroke-width="1.8"/></svg>`],['空调',`<svg width="26" height="26" viewBox="0 0 26 26"><path d="M13 3v20M4.3 8l17.4 10M4.3 18 21.7 8" stroke="#e6e6e6" stroke-width="1.8" stroke-linecap="round"/></svg>`]];
 const quick=qi.map((q,i)=>`<div class="a" style="left:${49+i*98-30}px;top:330px;width:60px;text-align:center"><div style="height:28px;display:flex;justify-content:center;align-items:center">${q[1]}</div><div class="cjk" style="font:400 12px 'Noto Sans CJK SC';color:#9a9aa0;margin-top:5px">${q[0]}</div></div>`).join('');
 const pShot=tapOn('shot',t),pLive=tapOn('live',t);
 const icCam=`<svg width="24" height="21" viewBox="0 0 30 26"><path d="M3 7h6l2.4-3.4h7.2L21 7h6v16H3z" fill="none" stroke="${GOLD}" stroke-width="2.2" stroke-linejoin="round"/><circle cx="15" cy="15" r="4.6" fill="none" stroke="${GOLD}" stroke-width="2.2"/></svg>`;
 const icLive=`<svg width="26" height="20" viewBox="0 0 32 24"><rect x="2" y="4" width="20" height="16" rx="3" fill="none" stroke="${GOLD}" stroke-width="2.2"/><path d="M23.5 10 30 5.5v13L23.5 14z" fill="${GOLD}"/></svg>`;
 const small=(x,ic,ti,su,pr)=>`<div class="a" style="left:${x}px;top:552px;width:180px;height:72px;border-radius:16px;background:${pr?'#2a2b30':'#16171a'}"><div class="a" style="left:16px;top:14px">${ic}</div><div class="a cjk" style="left:50px;top:13px;font:500 15px 'Noto Sans CJK SC';color:#efefef">${ti}</div><div class="a cjk" style="left:16px;top:44px;font:400 11.5px 'Noto Sans CJK SC';color:#7d7d83">${su}</div><div class="a" style="right:14px;top:16px;font:400 15px InterV;color:#5c5c62">›</div></div>`;
 const tabIc=(d)=>`<svg width="26" height="24" viewBox="0 0 26 24">${d}</svg>`;
 const tabs=[['发现',tabIc(`<path d="M3 11 13 3l10 8v10H3z" fill="none" stroke="#9a9aa0" stroke-width="1.7" stroke-linejoin="round"/>`)],['服务',tabIc(`<path d="M4 7h18l-2 13H6z" fill="none" stroke="#9a9aa0" stroke-width="1.7" stroke-linejoin="round"/><path d="M9 7a4 4 0 0 1 8 0" fill="none" stroke="#9a9aa0" stroke-width="1.7"/>`)],null,['商城',tabIc(`<rect x="4" y="5" width="18" height="15" rx="2" fill="none" stroke="#9a9aa0" stroke-width="1.7"/><path d="M9 9a4 4 0 0 0 8 0" fill="none" stroke="#9a9aa0" stroke-width="1.7"/>`)],['我的',tabIc(`<circle cx="13" cy="8" r="4.6" fill="none" stroke="#9a9aa0" stroke-width="1.7"/><path d="M4 21c1-4.6 4.6-7 9-7s8 2.4 9 7" fill="none" stroke="#9a9aa0" stroke-width="1.7" stroke-linecap="round"/>`)]];
 const tabbar=`<div class="a" style="left:0;top:${H-62}px;width:393px;height:62px;background:#0e0e10;border-top:.5px solid #222226">${tabs.map((x,i)=>{const cx=39+i*78.75;if(!x)return `<div class="a" style="left:${cx-24}px;top:-10px;width:48px;height:48px;border-radius:24px;background:linear-gradient(145deg,#e6c487,#b88d48);display:flex;align-items:center;justify-content:center;box-shadow:0 3px 10px rgba(0,0,0,.5)"><svg width="26" height="26" viewBox="0 0 24 24"><path d="M2.6 16c2.7-6 6-9 9.4-9s6.7 3 9.4 9" fill="none" stroke="#1a1408" stroke-width="2.3" stroke-linecap="round"/><path d="M7.4 16c1.5-2.8 3-4.1 4.6-4.1s3.1 1.3 4.6 4.1" fill="none" stroke="#1a1408" stroke-width="2.3" stroke-linecap="round"/></svg></div><div class="a cjk" style="left:${cx-20}px;top:41px;width:40px;text-align:center;font:500 10.5px 'Noto Sans CJK SC';color:${GOLD}">爱车</div>`;return `<div class="a" style="left:${cx-24}px;top:7px;width:48px;text-align:center"><div style="display:flex;justify-content:center">${x[1]}</div><div class="cjk" style="font:400 10.5px 'Noto Sans CJK SC';color:#9a9aa0;margin-top:1px">${x[0]}</div></div>`;}).join('')}</div>`;
 const RG=rangeAt(t);
 return `<div class="L" style="background:#000"><div class="a" style="left:0;top:0;width:393px;height:330px;background:linear-gradient(#1b2436,#0d1018 60%,#000)"></div>
 <div class="a" style="left:22px;top:56px;font:600 46px/1 InterV;color:#f2f2f2;letter-spacing:-1px">${RG[0]}<span style="font:500 17px InterV;margin-left:4px;letter-spacing:0">km</span></div>
 <div class="a" style="left:150px;top:60px;font:500 11px InterV;color:#8f96a3">CLTC</div><div class="a" style="left:150px;top:78px;font:500 13px InterV;color:#8f96a3">${RG[1]}%</div>
 <div class="a" style="left:22px;top:112px;width:160px;height:3px;border-radius:2px;background:rgba(255,255,255,.18)"><div style="width:${160*RG[1]/100}px;height:3px;border-radius:2px;background:#e8e8ec"></div></div>
 <svg class="a" style="right:64px;top:60px" width="22" height="22" viewBox="0 0 22 22"><path d="M2 7V2h5M15 2h5v5M20 15v5h-5M7 20H2v-5M2 11h18" stroke="#e6e6e6" stroke-width="1.7" fill="none" stroke-linecap="round"/></svg><svg class="a" style="right:22px;top:59px" width="24" height="24" viewBox="0 0 24 24"><path d="M12 2.5 20.2 7.2v9.6L12 21.5 3.8 16.8V7.2z" fill="none" stroke="#e6e6e6" stroke-width="1.7" stroke-linejoin="round"/><circle cx="12" cy="12" r="3.2" fill="none" stroke="#e6e6e6" stroke-width="1.7"/></svg>
 <div class="a cjk" style="right:22px;top:98px;font:400 13px 'Noto Sans CJK SC';color:#d8d8dc">${chip}</div>
 <img src="${TH}car.png" class="a" style="left:${196.5-128}px;top:128px;width:256px;height:172px;object-fit:contain">
 <div class="a cjk" style="left:0;width:393px;top:298px;text-align:center;font:400 12.5px 'InterV','Noto Sans CJK SC';color:#8f96a3">${moving?`${spd} km/h · 绕城高速`:'P 挡 · 已熄火 · 地下车库 B2'}</div>
 ${quick}${seatCard(st,t,386)}
 ${small(12,icCam,'车内拍照','拍照时车内将语音提示',pShot)}${small(201,icLive,'实时查看车内','单次 15 秒 · 红外夜视',pLive)}
 ${tabbar}${carDialog(t)}${carLoading(t)}${homeBar()}</div>`;
}
function carDialog(t){
 const d=F.car.dialogs.find(x=>t>=x.s&&t<x.e+0.2);if(!d)return '';
 const p=Math.min(eo(prog(t,d.s,d.s+0.2)),1-prog(t,d.e,d.e+0.2));const pr=t>=d.tap-0.12&&t<d.e;
 return `<div class="L" style="background:rgba(0,0,0,${0.55*p});z-index:20"></div><div class="a" style="left:${196.5-150}px;top:${H/2-92}px;width:300px;height:184px;border-radius:16px;background:#1f2025;z-index:21;opacity:${p};transform:scale(${lerp(1.06,1,p)})"><div class="a cjk" style="left:0;width:300px;top:20px;text-align:center;font:500 17px 'Noto Sans CJK SC';color:#f2f2f2">车内拍照</div><div class="a cjk" style="left:24px;width:252px;top:52px;text-align:center;font:400 14px/22px 'Noto Sans CJK SC';color:#a8a8ae">拍照时，车内将播放语音提示“车主正在查看车内”，是否继续？</div><div class="a" style="left:0;top:132px;width:300px;height:.5px;background:#34353b"></div><div class="a" style="left:150px;top:132px;width:.5px;height:52px;background:#34353b"></div><div class="a cjk" style="left:0;top:132px;width:150px;height:52px;line-height:52px;text-align:center;font:400 16px 'Noto Sans CJK SC';color:#c9c9ce">取消</div><div class="a cjk" style="left:150px;top:132px;width:150px;height:52px;line-height:52px;text-align:center;font:500 16px 'Noto Sans CJK SC';color:${GOLD};${pr?'background:#2b2c31;border-radius:0 0 16px 0':''}">确认</div></div>`;
}
function spinner(c='#e6e6e6',t=0,size=30){const n=8;return `<svg width="${size}" height="${size}" viewBox="0 0 30 30">${[...Array(n).keys()].map(i=>{const a=i/n*Math.PI*2;const k=(i-Math.floor(t*10))%n;const o=0.2+0.8*(((k%n)+n)%n)/(n-1);return `<line x1="${15+Math.cos(a)*6}" y1="${15+Math.sin(a)*6}" x2="${15+Math.cos(a)*12}" y2="${15+Math.sin(a)*12}" stroke="${c}" stroke-width="2.6" stroke-linecap="round" opacity="${o.toFixed(2)}"/>`;}).join('')}</svg>`;}
function carLoading(t){
 const l=F.car.loads.find(x=>t>=x.s&&t<x.e);if(!l)return '';const p=eo(prog(t,l.s,l.s+0.15));
 return `<div class="L" style="background:rgba(0,0,0,${0.4*p});z-index:22"></div><div class="a" style="left:${196.5-70}px;top:${H/2-60}px;width:140px;height:120px;border-radius:14px;background:rgba(32,33,38,.96);z-index:23;opacity:${p};display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px">${spinner('#e6e6e6',t)}<div class="cjk" style="font:400 13.5px 'Noto Sans CJK SC';color:#dcdce0">正在拍摄…</div></div>`;
}
const PHOTO_INFO={ir1:['行驶中 · 代驾模式','绕城高速 · 嘉闵段'],ir2:['行驶中 · 代驾模式','绕城高速 · 嘉闵段'],garage:['已熄火 · 右后门已打开','地下车库 B2']};
function irPhoto(src,shot,t,x,y,w,h){
 return `<div class="a" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;overflow:hidden;background:#000"><img src="${TH}${src}_full.jpg" style="width:100%;height:100%;object-fit:cover;filter:contrast(1.05)">${IRN(0.4,0.2)}<div class="a" style="left:10px;bottom:8px;font:500 11px InterV;color:rgba(255,255,255,.88);letter-spacing:.3px;text-shadow:0 0 2px #000">2026-11-07 ${shot}</div><div class="a" style="right:10px;top:8px;font:600 10px InterV;color:rgba(255,255,255,.8);letter-spacing:.6px;text-shadow:0 0 2px #000">CABIN CAM · IR</div></div>`;
}
function carPhoto(t,spec){
 const info=PHOTO_INFO[spec.src];const sh=F.car.share;
 const rows=[['拍摄时间',`2026-11-07 ${spec.shot}`],['车辆状态',info[0]],['车辆位置',info[1]],['拍摄方式','车内摄像头 · 红外夜视']].map((r,i)=>`<div class="a cjk" style="left:28px;top:${370+i*34}px;font:400 14px 'Noto Sans CJK SC';color:#8b8b90">${r[0]}</div><div class="a cjk" style="right:28px;top:${370+i*34}px;font:400 14px 'InterV','Noto Sans CJK SC';color:#e2e2e6">${r[1]}</div>`).join('');
 const prShare=tapOn('share',t);
 const btn=(x,w,l,gold,pr)=>`<div class="a cjk" style="left:${x}px;top:${H-112}px;width:${w}px;height:46px;border-radius:23px;line-height:46px;text-align:center;font:500 15px 'Noto Sans CJK SC';${gold?`background:${pr?'#b8935a':GOLD};color:#1a1408`:`background:#1f2024;color:#e2e2e6`}">${l}</div>`;
 let sheet='';
 if(spec.src==='ir2'&&t>=sh.s&&t<sh.e+0.3){const p=Math.min(eo(prog(t,sh.s,sh.s+0.25)),1-prog(t,sh.e,sh.e+0.3));const pr=t>=sh.tap-0.12;
  const it=(x,ic,l,hl)=>`<div class="a" style="left:${x-30}px;top:56px;width:60px;text-align:center"><div style="width:52px;height:52px;margin:0 auto;border-radius:13px;overflow:hidden;${hl?'filter:brightness(.7)':''}">${ic}</div><div class="cjk" style="font:400 11.5px 'Noto Sans CJK SC';color:#b8b8be;margin-top:7px">${l}</div></div>`;
  const tile=(c,s)=>`<div style="width:52px;height:52px;background:${c};display:flex;align-items:center;justify-content:center">${s}</div>`;
  sheet=`<div class="L" style="background:rgba(0,0,0,${0.45*p});z-index:20"></div><div class="a" style="left:0;top:${H-(206)*p}px;width:393px;height:206px;border-radius:16px 16px 0 0;background:#1c1d21;z-index:21"><div class="a cjk" style="left:0;width:393px;top:18px;text-align:center;font:500 15px 'Noto Sans CJK SC';color:#e8e8ec">分享到</div>${it(64,`<img src="${IC}wechat.png" style="width:52px;height:52px;display:block">`,'微信好友',pr)}${it(152,tile('#2b2c31',`<svg width="26" height="26" viewBox="0 0 26 26"><circle cx="13" cy="13" r="10" fill="none" stroke="#e6e6e6" stroke-width="1.8"/><circle cx="13" cy="13" r="3.4" fill="#e6e6e6"/></svg>`),'朋友圈')}${it(240,tile('#2b2c31',`<svg width="24" height="24" viewBox="0 0 24 24"><path d="M12 3v12M7 10l5 5 5-5M4 20h16" stroke="#e6e6e6" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`),'保存图片')}${it(328,tile('#2b2c31',`<svg width="24" height="24" viewBox="0 0 24 24"><path d="M10 14a4 4 0 0 0 5.6 0l3-3a4 4 0 0 0-5.6-5.6l-1 1M14 10a4 4 0 0 0-5.6 0l-3 3a4 4 0 0 0 5.6 5.6l1-1" stroke="#e6e6e6" stroke-width="1.8" fill="none" stroke-linecap="round"/></svg>`),'复制链接')}<div class="a cjk" style="left:0;width:393px;top:150px;text-align:center;font:400 15px 'Noto Sans CJK SC';color:#9a9aa0">取消</div></div>`;}
 return `<div class="L" style="background:#0b0b0d">${carNav('车内照片','')}${irPhoto(spec.src,spec.shot,t,0,106,393,221)}<div class="a" style="left:12px;top:350px;width:369px;height:150px;border-radius:16px;background:#16171a"></div>${rows}<div class="a cjk" style="left:0;width:393px;top:514px;text-align:center;font:400 12px 'Noto Sans CJK SC';color:#6c6c72">为保护隐私，照片仅保存 24 小时</div>${btn(18,110,'保存',false)}${btn(141,111,'分享',true,prShare)}${btn(265,110,'重新拍摄',false)}${sheet}${homeBar()}</div>`;
}
function liveVT(L,t){
 if(L.freeze){const [fs,fe,rv]=L.freeze;if(t<fs)return t-L.start;if(t<fe)return fs-L.start;return rv+(t-fe);}
 return t-L.start;
}
function liveFrame(L,n,t){
 let i=Math.floor(liveVT(L,t)*L.fps);
 // a few dropped frames: hold the previous frame for a moment
 const k=Math.floor(i/9);if(hash(k+3+n*17)>0.72&&i%9<3)i=k*9;
 i=clamp(i,0,L.frames-1);return `${A}video/frames/live${n}/f${String(i+1).padStart(3,'0')}.jpg`;
}
function carLive(t,n){
 const L=F.live[n-1];const st=n===1?'alert':'alert2';
 const connecting=t<L.start;
 const fz=!!L.freeze&&t>=L.freeze[0]&&t<L.freeze[1];
 const frozen=t>=L.end||fz;
 const tt=t>=L.end?L.end-0.01:(fz?L.freeze[0]:t);
 const left=clamp(15-Math.floor(Math.max(0,tt-L.start)),0,15);
 let box;
 if(connecting)box=`<div class="a" style="inset:0;background:#050506;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px">${spinner('#cfcfd4',t,28)}<div class="cjk" style="font:400 12.5px 'Noto Sans CJK SC';color:#9a9aa0">正在连接车内摄像头…</div></div>`;
 else box=`<img src="${liveFrame(L,n,tt)}" style="width:100%;height:100%;object-fit:cover">${IRN(frozen?0.5:t,0.24)}<div class="a" style="left:10px;top:9px;display:flex;align-items:center;gap:5px;font:600 10.5px InterV;color:#fff;text-shadow:0 0 2px #000"><span style="width:7px;height:7px;border-radius:4px;background:#ff3b30;display:inline-block;opacity:${frozen?0.4:(Math.floor(t*2)%2?1:.35)}"></span>LIVE</div><div class="a" style="right:10px;top:9px;font:600 10px InterV;color:rgba(255,255,255,.82);letter-spacing:.5px;text-shadow:0 0 2px #000">15 FPS · 标清</div><div class="a" style="left:10px;bottom:8px;font:500 11px InterV;color:rgba(255,255,255,.88);text-shadow:0 0 2px #000">2026-11-07 ${clockFull(tt)}</div>${frozen?`<div class="a" style="inset:0;background:rgba(0,0,0,.42);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px">${spinner('#e6e6e6',t,26)}<div class="cjk" style="font:400 13px 'Noto Sans CJK SC';color:#e8e8ec">网络不佳，画面已暂停</div></div>`:''}`;
 const sub=connecting?'连接中':`剩余 00:${pad(left)}`;
 return `<div class="L" style="background:#0b0b0d">${carNav('实时查看车内',sub)}<div class="a" style="left:0;top:106px;width:393px;height:221px;overflow:hidden;background:#000">${box}</div>
 <div class="a cjk" style="left:12px;top:338px;width:369px;padding:10px 14px;border-radius:12px;background:#1a1712;font:400 12.5px/19px 'Noto Sans CJK SC';color:#c9b58f">查看期间，车内中控屏会显示“车主正在查看车内”</div>
 ${seatCard(st,t,394,150)}
 <div class="a cjk" style="left:24px;top:${H-112}px;width:345px;height:46px;border-radius:23px;line-height:46px;text-align:center;font:500 15px 'Noto Sans CJK SC';background:#1f2024;color:#ff6961">结束查看</div>${homeBar()}</div>`;
}
function carView(spec,t){return spec.page==='photo'?carPhoto(t,spec):spec.page==='live'?carLive(t,spec.n||1):carHome(t);}
// ---------- 安途代驾 (WeChat mini program, light) ----------
function mpLogo(s=18){return `<div style="width:${s}px;height:${s}px;border-radius:${s/2}px;background:#1677ff;display:flex;align-items:center;justify-content:center;flex:0 0 ${s}px"><svg width="${s*0.62}" height="${s*0.62}" viewBox="0 0 20 20"><path d="M3 13.5 4.6 8.6C5 7.4 6 6.8 7.2 6.8h5.6c1.2 0 2.2.6 2.6 1.8l1.6 4.9v3H3z" fill="#fff"/><circle cx="6.4" cy="13.2" r="1.3" fill="#1677ff"/><circle cx="13.6" cy="13.2" r="1.3" fill="#1677ff"/></svg></div>`;}
const MAPC={x:160,y:190};
const LOOPC={x:200,y:230,r:33};
function lapsAt(t){const p=F.mp.laps;if(!p||!p.length)return 1;if(t<=p[0][0])return p[0][1];for(let i=1;i<p.length;i++)if(t<p[i][0]){const a=p[i-1],b=p[i];return a[1]+(b[1]-a[1])*(t-a[0])/(b[0]-a[0]);}return p[p.length-1][1];}
function bez(p0,p1,p2,p3,n){const o=[];for(let i=0;i<=n;i++){const u=i/n,v=1-u;o.push([v*v*v*p0[0]+3*v*v*u*p1[0]+3*v*u*u*p2[0]+u*u*u*p3[0],v*v*v*p0[1]+3*v*v*u*p1[1]+3*v*u*u*p2[1]+u*u*u*p3[1]]);}return o;}
function ptsD(p){return 'M'+p.map(q=>q[0].toFixed(1)+' '+q[1].toFixed(1)).join(' L');}
// the planned way home from the ramp exit: onto 绕城高速 eastbound, off at 龙华东路, north to the pin
const EXIT_ROUTE=(()=>{const {x,y,r}=LOOPC;const e=[x,y-r];let p=bez(e,[x+12,e[1]-3],[x+20,193],[x+34,193],8);
 p=p.concat([[262,193],[300,193]]);p=p.concat(bez([300,193],[326,193],[342,182],[342,160],10).slice(1));p.push([342,104]);return p;})();
function chevrons(p,step=15){let g='',acc=step*0.6;for(let i=1;i<p.length;i++){const a=p[i-1],b=p[i];const dx=b[0]-a[0],dy=b[1]-a[1];const L=Math.hypot(dx,dy);if(L<1e-6)continue;let d=acc;while(d<L){const x=a[0]+dx*d/L,y=a[1]+dy*d/L;const ang=Math.atan2(dy,dx)*180/Math.PI;g+=`<path d="M-1.8 -2.4 L1.6 0 L-1.8 2.4" transform="translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${ang.toFixed(0)})" fill="none" stroke="#fff" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round"/>`;d+=step;}acc=d-L;}return g;}
function carIcon(x,y,rot,s=1){return `<g transform="translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${rot.toFixed(1)}) scale(${s})"><rect x="-6.6" y="-11" width="13.2" height="22" rx="4.6" fill="rgba(0,0,0,.22)" transform="translate(.8 1.2)"/><rect x="-6.4" y="-11" width="12.8" height="22" rx="4.6" fill="#fdfdfd" stroke="#c9ced6" stroke-width=".6"/><path d="M-4.9 -4.6 Q0 -6.6 4.9 -4.6 L4.2 -1.2 L-4.2 -1.2 Z" fill="#3b4250"/><path d="M-4.3 5.2 L4.3 5.2 L4.8 7.8 Q0 9.2 -4.8 7.8 Z" fill="#596273"/><rect x="-4.6" y="-0.6" width="9.2" height="5.4" rx="1.2" fill="#eceff3"/></g>`;}
function baseMap(mini){
 const C=MAPC;let g=`<rect width="393" height="340" fill="#f3f4f6"/>`;
 // river and parks
 g+=`<path d="M -10 262 C 40 270, 70 300, 92 350" fill="none" stroke="#cfe3f6" stroke-width="15"/>`;
 g+=`<path d="M 300 226 L 384 222 L 388 290 L 304 294 Z" fill="#d7eed7"/><path d="M 20 20 L 70 18 L 72 50 L 22 52 Z" fill="#d7eed7"/>`;
 // street blocks
 const blocks=[[36,46,48,42],[96,46,50,42],[192,46,46,42],[256,46,40,42],[350,46,40,42],[36,101,48,32],[96,101,50,32],[256,101,40,32],[350,101,40,32],[256,146,40,34],[350,146,40,40],[36,146,48,30],[96,146,40,26],[256,206,36,14],[36,206,40,40],[256,266,40,26],[96,266,40,26],[196,300,46,30],[256,300,40,30],[350,300,40,30],[36,306,40,30]];
 g+=blocks.map(b=>`<rect x="${b[0]}" y="${b[1]}" width="${b[2]}" height="${b[3]}" rx="2" fill="#e8eaee"/>`).join('');
 // local streets (white with a soft casing); they stop at the interchange
 const st=[[30,-5,30,350],[90,-5,90,182],[90,262,90,350],[250,-5,250,150],[250,262,250,350],[300,-5,300,186],[300,198,300,350],[342,-5,342,186],[342,198,342,350],[386,-5,386,350],[-5,40,393,40],[-5,95,150,95],[214,95,393,95],[-5,140,110,140],[246,140,393,140],[-5,260,92,260],[262,260,393,260],[-5,298,104,298],[196,298,393,298]];
 const wide=s=>(s[0]===342||s[1]===95)?7.4:5.6;
 g+=st.map(s=>`<line x1="${s[0]}" y1="${s[1]}" x2="${s[2]}" y2="${s[3]}" stroke="#dcdfe4" stroke-width="${wide(s)+2.2}" stroke-linecap="round"/>`).join('');
 g+=st.map(s=>`<line x1="${s[0]}" y1="${s[1]}" x2="${s[2]}" y2="${s[3]}" stroke="#fff" stroke-width="${wide(s)}" stroke-linecap="round"/>`).join('');
 // the land inside the interchange: no blocks, no streets
 g+=`<rect x="${C.x-114}" y="${C.y-114}" width="228" height="228" rx="46" fill="#eaf0e6"/>`;
 // interchange ramps (four loops + four outer ramps), then the two expressways on top
 const ramps=[];
 for(const [sx,sy] of [[1,1],[1,-1],[-1,1],[-1,-1]]){
  ramps.push(`<circle cx="${C.x+40*sx}" cy="${C.y+40*sy}" r="33" fill="none" STROKE/>`);
  ramps.push(`<path d="M ${C.x+6*sx} ${C.y+104*sy} Q ${C.x+84*sx} ${C.y+84*sy} ${C.x+104*sx} ${C.y+6*sy}" fill="none" STROKE/>`);
 }
 g+=ramps.map(r=>r.replace('STROKE','stroke="#efc56a" stroke-width="8.6"')).join('')+ramps.map(r=>r.replace('STROKE','stroke="#ffe6a3" stroke-width="5.8"')).join('');
 g+=`<line x1="-10" y1="${C.y}" x2="403" y2="${C.y}" stroke="#eab14a" stroke-width="15"/><line x1="${C.x}" y1="-10" x2="${C.x}" y2="350" stroke="#eab14a" stroke-width="15"/>`;
 g+=`<line x1="-10" y1="${C.y}" x2="403" y2="${C.y}" stroke="#ffd36a" stroke-width="11.5"/><line x1="${C.x}" y1="-10" x2="${C.x}" y2="350" stroke="#ffd36a" stroke-width="11.5"/>`;
 g+=`<line x1="-10" y1="${C.y}" x2="403" y2="${C.y}" stroke="#f3bd52" stroke-width=".8" stroke-dasharray="6 6"/><line x1="${C.x}" y1="-10" x2="${C.x}" y2="350" stroke="#f3bd52" stroke-width=".8" stroke-dasharray="6 6"/>`;
 // labels (white halo like a real map)
 const lab=(x,y,txt,sz=9.5,col='#8b919a',w=400,rot=0)=>`<text x="${x}" y="${y}" ${rot?`transform="rotate(${rot} ${x} ${y})"`:''} font-family="Noto Sans CJK SC" font-size="${sz}" font-weight="${w}" fill="${col}" stroke="#fff" stroke-width="2.6" paint-order="stroke" stroke-linejoin="round">${txt}</text>`;
 if(!mini){
  g+=lab(22,186,'绕城高速',10,'#9a6a0e',600)+lab(306,186,'绕城高速',10,'#9a6a0e',600)+lab(156,24,'嘉闵高架',10,'#9a6a0e',600,90)+lab(156,300,'嘉闵高架',10,'#9a6a0e',600,90);
  g+=lab(96,170,'嘉闵立交',10.5,'#5f6773',500);
  g+=lab(346,206,'龙华东路',9.5,'#7d848e',400,90)+lab(196,91,'中山南路')+lab(34,136,'漕宝路')+lab(26,330,'虹梅南路',9.5,'#8b919a',400,-90)+lab(258,256,'春申路');
  g+=lab(318,262,'华泾公园',9.5,'#5f9b63')+lab(40,276,'淀浦河',9,'#6f9cc8')+lab(40,70,'梅陇镇')+lab(262,70,'锦江乐园')+lab(354,126,'景谷苑');
  g+=[[52,78],[270,78],[360,120]].map(p=>`<circle cx="${p[0]-6}" cy="${p[1]-3.5}" r="2.3" fill="#a9b0ba"/>`).join('');
 }
 return g;
}
function mapSvg(t,w,h,mini){
 if(mini){
  // trip card: the driver on his way to the restaurant
  const route=[[30,250],[30,95],[150,95]];
  return `<svg width="${w}" height="${h}" viewBox="0 30 220 163" preserveAspectRatio="xMidYMid slice">${baseMap(true)}<path d="${ptsD(route)}" fill="none" stroke="#1f9d5a" stroke-width="7.4" stroke-linejoin="round" stroke-linecap="round"/><path d="${ptsD(route)}" fill="none" stroke="#2fc274" stroke-width="5.4" stroke-linejoin="round" stroke-linecap="round"/>${chevrons(route,14)}${carIcon(30,170,0,.85)}<g transform="translate(150 95)"><circle r="6.5" fill="#1677ff" stroke="#fff" stroke-width="2"/><text y="3.4" text-anchor="middle" font-family="Noto Sans CJK SC" font-size="8.5" font-weight="700" fill="#fff">起</text></g></svg>`;
 }
 const {x,y,r}=LOOPC;const Lp=lapsAt(t);const fr=Lp-Math.floor(Lp);
 // the car goes clockwise round the south-east loop; lap fraction 0 = the exit at the top of the loop
 const th=-Math.PI/2+fr*2*Math.PI;const cx=x+r*Math.cos(th),cy=y+r*Math.sin(th);
 const rot=Math.atan2(Math.cos(th),-Math.sin(th))*180/Math.PI+90;
 const arc=[];const n=Math.max(2,Math.round((1-fr)*60));for(let i=0;i<=n;i++){const a=th+(i/n)*(1-fr)*2*Math.PI;arc.push([x+r*Math.cos(a),y+r*Math.sin(a)]);}
 const route=arc.concat(EXIT_ROUTE.slice(1));
 // traffic colours along the remaining route: mostly smooth, a slow stretch on 绕城高速
 const seg=(p0,p1)=>route.filter(q=>q[0]>=p0&&q[0]<=p1&&Math.abs(q[1]-193)<1);
 const slow=seg(262,300);
 // travelled track (grey): up 嘉闵高架 from the south, into the loop, and every lap of the loop
 const went=[[164,350],[164,262],...bez([164,262],[164,248],[166,232],[x-r,y],8).slice(1)];
 return `<svg width="${w}" height="${h}" viewBox="0 0 393 340" preserveAspectRatio="xMidYMid slice">${baseMap(false)}
 <path d="${ptsD(went)}" fill="none" stroke="#9aa3b0" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity=".9"/>
 <circle cx="${x}" cy="${y}" r="${r}" fill="none" stroke="#9aa3b0" stroke-width="6" opacity=".9"/>
 <path d="${ptsD(route)}" fill="none" stroke="#18975a" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
 <path d="${ptsD(route)}" fill="none" stroke="#2ec372" stroke-width="5.8" stroke-linecap="round" stroke-linejoin="round"/>
 ${slow.length>1?`<path d="${ptsD(slow)}" fill="none" stroke="#f5b829" stroke-width="5.8" stroke-linecap="round"/>`:''}
 ${chevrons(route,15)}
 <g transform="translate(342 104)"><path d="M0 0c-9-11-13-17-13-23a13 13 0 0 1 26 0c0 6-4 12-13 23z" fill="#ff6a1a" stroke="#fff" stroke-width="1.4"/><text x="0" y="-19" text-anchor="middle" font-family="Noto Sans CJK SC" font-size="11" font-weight="700" fill="#fff">终</text></g>
 ${carIcon(cx,cy,rot,1.05)}
 </svg>`;
}
function tripCard(t){
 const pr=tapOn('trip',t);
 return `<div style="width:226px;border-radius:6px;background:${pr?'#333':'#2c2c2c'};overflow:hidden;padding:10px 12px 0"><div style="display:flex;align-items:center;gap:6px">${mpLogo(17)}<span class="cjk" style="font:400 12.5px 'Noto Sans CJK SC';color:#9a9a9a">安途代驾</span></div><div class="cjk" style="margin-top:7px;font:400 14.5px/21px 'Noto Sans CJK SC';color:#e6e6e6">我的代驾行程，邀你实时查看</div><div style="margin-top:8px;width:202px;height:150px;border-radius:4px;overflow:hidden;position:relative">${mapSvg(t,202,150,true)}<div class="cjk" style="position:absolute;left:6px;right:6px;bottom:6px;padding:5px 8px;border-radius:5px;background:rgba(255,255,255,.95);font:400 11px/15px 'Noto Sans CJK SC';color:#333"><b style="font-weight:600">王师傅</b> · 工号 0371<br><span style="color:#19a463">司机已接单，约 5 分钟到达</span></div></div><div style="margin-top:9px;height:30px;border-top:.5px solid #3a3a3a;display:flex;align-items:center;gap:5px"><svg width="13" height="13" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6.2" fill="none" stroke="#8a8a8a" stroke-width="1.2"/><path d="M4.6 8.6c0-1.6 2.4-1.6 2.4-3.2a1.2 1.2 0 0 1 2.4 0" stroke="#8a8a8a" stroke-width="1.2" fill="none"/></svg><span class="cjk" style="font:400 11px 'Noto Sans CJK SC';color:#8a8a8a">小程序</span></div></div>`;
}
function mpView(t){
 const al=F.mp.alert;const pc=tapOn('contact',t);
 const Lp=lapsAt(t);const etaT=Lp<2.5?'00:37':'00:38';const km=(27.4+0.35*(Lp-1)).toFixed(1);
 const capsule=`<div class="a" style="right:7px;top:57px;width:87px;height:32px;border-radius:16px;border:.5px solid rgba(0,0,0,.14);background:rgba(255,255,255,.7);display:flex;align-items:center"><div style="width:43px;display:flex;justify-content:center;gap:3px">${[0,1,2].map(i=>`<div style="width:${i===1?6:4.5}px;height:${i===1?6:4.5}px;border-radius:3px;background:#111"></div>`).join('')}</div><div style="width:.5px;height:18px;background:rgba(0,0,0,.18)"></div><div style="width:43px;display:flex;justify-content:center"><svg width="18" height="18" viewBox="0 0 18 18"><circle cx="9" cy="9" r="7.4" fill="none" stroke="#111" stroke-width="1.6"/><circle cx="9" cy="9" r="2.6" fill="#111"/></svg></div></div>`;
 const nav=`<div class="a" style="left:0;top:0;width:393px;height:98px;background:#fff"><svg class="a" style="left:16px;top:63px" width="20" height="20" viewBox="0 0 20 20"><path d="M2.5 9 10 2.6 17.5 9v8.4h-15z" fill="none" stroke="#111" stroke-width="1.7" stroke-linejoin="round"/><path d="M8 17.4v-5h4v5" stroke="#111" stroke-width="1.7" fill="none"/></svg><div class="a cjk" style="left:0;width:393px;top:62px;text-align:center;font:500 17px 'Noto Sans CJK SC';color:#111">行程详情</div>${capsule}</div>`;
 const map=`<div class="a" style="left:0;top:98px;width:393px;height:340px;overflow:hidden">${mapSvg(t,393,340,false)}</div>`;
 const notice=`<div class="a cjk" style="left:12px;top:108px;width:369px;padding:8px 12px;border-radius:8px;background:#fff7e6;border:.5px solid #ffd591;font:400 12.5px/18px 'Noto Sans CJK SC';color:#d46b08;box-shadow:0 2px 8px rgba(0,0,0,.06)">车辆偏离推荐路线，预计到达时间已更新为 ${etaT}</div>`;
 const mins=Lp<2.5?13:14;
 const eta=`<div class="a" style="left:0;width:393px;top:${98+50}px;display:flex;justify-content:center"><div style="display:flex;border-radius:8px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.16)"><div class="cjk" style="padding:6px 9px;background:#19b46b;font:600 13px 'InterV','Noto Sans CJK SC';color:#fff">${mins}分钟</div><div class="cjk" style="padding:6px 10px;background:#fff;font:500 13px 'InterV','Noto Sans CJK SC';color:#222">距终点 8.6公里</div></div></div>`;
 const safety=`<div class="a" style="left:12px;top:378px;height:30px;padding:0 11px 0 8px;border-radius:15px;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.14);display:flex;align-items:center;gap:5px"><svg width="15" height="16" viewBox="0 0 16 18"><path d="M8 1 15 3.6v5c0 4.2-3 7.4-7 8.4-4-1-7-4.2-7-8.4v-5z" fill="#1677ff"/><path d="M5 9l2.2 2.2L11.2 7" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg><span class="cjk" style="font:500 12.5px 'Noto Sans CJK SC';color:#222">安全中心</span></div><div class="a" style="right:12px;top:376px;width:34px;height:34px;border-radius:17px;background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.14);display:flex;align-items:center;justify-content:center"><svg width="18" height="18" viewBox="0 0 18 18"><circle cx="9" cy="9" r="5.6" fill="none" stroke="#333" stroke-width="1.6"/><circle cx="9" cy="9" r="2" fill="#333"/><path d="M9 0.8v2.6M9 14.6v2.6M0.8 9h2.6M14.6 9h2.6" stroke="#333" stroke-width="1.6" stroke-linecap="round"/></svg></div>`;
 const btn=(x,ic,l,c,pr)=>`<div class="a" style="left:${x-56}px;top:610px;width:112px;height:44px;border-radius:10px;background:${pr?'#e6e8eb':'#f5f6f8'};display:flex;align-items:center;justify-content:center;gap:6px">${ic}<span class="cjk" style="font:500 13.5px 'Noto Sans CJK SC';color:${c}">${l}</span></div>`;
 const icAlarm=`<svg width="16" height="18" viewBox="0 0 16 18"><path d="M8 1 15 3.6v5c0 4.2-3 7.4-7 8.4-4-1-7-4.2-7-8.4v-5z" fill="#ff4d4f"/><path d="M8 5v4.6M8 12.2v.4" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/></svg>`;
 const icPhone=`<svg width="16" height="16" viewBox="0 0 16 16"><path d="M4.2 1.2 6.4 4 5 5.8c.8 1.9 2.3 3.4 4.2 4.2L11 8.6l2.8 2.2-.9 3c-.2.6-.8 1-1.5.9C6 14.2 1.8 10 1.3 4.6c-.1-.7.3-1.3.9-1.5z" fill="#1677ff"/></svg>`;
 const icShare=`<svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 10V1.6M4.8 4.6 8 1.4l3.2 3.2M2 8.4v5.6h12V8.4" stroke="#333" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
 const sheet=`<div class="a" style="left:0;top:424px;width:393px;height:${H-424}px;border-radius:16px 16px 0 0;background:#fff;box-shadow:0 -4px 16px rgba(0,0,0,.08)">
 <div class="a" style="left:${196.5-18}px;top:7px;width:36px;height:4px;border-radius:2px;background:#e1e3e6"></div>
 <div class="a cjk" style="left:18px;top:22px;padding:2px 8px;border-radius:4px;background:#e8f7ef;font:500 12px 'Noto Sans CJK SC';color:#19a463">代驾中</div><div class="a cjk" style="left:78px;top:24px;font:400 12.5px 'Noto Sans CJK SC';color:#8c8c8c">已行驶 ${km} 公里 · 行程录音保护中</div>
 <div class="a" style="left:18px;top:58px;width:52px;height:52px;border-radius:26px;background:#eef0f3;overflow:hidden"><svg width="52" height="52" viewBox="0 0 52 52"><circle cx="26" cy="21" r="9" fill="#c5cad3"/><path d="M9 50c2-11 8.4-16 17-16s15 5 17 16z" fill="#c5cad3"/></svg></div>
 <div class="a cjk" style="left:82px;top:60px;font:600 18px 'Noto Sans CJK SC';color:#111">王师傅</div><div class="a cjk" style="left:82px;top:88px;font:400 12.5px 'InterV','Noto Sans CJK SC';color:#8c8c8c"><span style="color:#faad14">★</span> 4.9 · 代驾 8326 单 · 工号 0371</div>
 <div class="a" style="right:18px;top:58px;text-align:right"><div class="cjk" style="font:600 17px 'InterV','Noto Sans CJK SC';color:#111;letter-spacing:.5px">沪A·D7K**</div><div class="cjk" style="font:400 12px 'Noto Sans CJK SC';color:#8c8c8c;margin-top:4px">白色 · 行云 S7</div></div>
 <div class="a" style="left:18px;top:126px;width:357px;height:.5px;background:#eee"></div>
 <div class="a cjk" style="left:18px;top:138px;font:400 12.5px 'Noto Sans CJK SC';color:#8c8c8c">起点 · 金樽酒楼（中山南路店）</div><div class="a cjk" style="left:18px;top:160px;font:400 12.5px 'Noto Sans CJK SC';color:#8c8c8c">终点 · 家</div>
 </div>${btn(72,icAlarm,'一键报警','#ff4d4f')}${btn(196.5,icPhone,'联系司机','#1677ff',pc)}${btn(321,icShare,'分享行程','#333')}`;
 let alert='';
 if(t>=al.s&&t<al.e+0.2){const p=Math.min(eo(prog(t,al.s,al.s+0.22)),1-prog(t,al.e,al.e+0.2));const pr=t>=al.tap-0.12&&t<al.e;
  alert=`<div class="L" style="background:rgba(0,0,0,${0.3*p});z-index:20"></div><div class="a" style="left:${196.5-135}px;top:${H/2-62}px;width:270px;height:124px;border-radius:14px;background:rgba(242,242,247,.96);backdrop-filter:blur(20px);z-index:21;opacity:${p};transform:scale(${lerp(1.12,1,eo(p))})"><div class="a" style="left:0;width:270px;top:24px;text-align:center;font:600 17px InterV;color:#000">170 3291 0371</div><div class="a cjk" style="left:0;width:270px;top:50px;text-align:center;font:400 13px 'Noto Sans CJK SC';color:#3c3c43">虚拟号码，30 分钟内有效</div><div class="a" style="left:0;top:80px;width:270px;height:.5px;background:rgba(60,60,67,.3)"></div><div class="a" style="left:135px;top:80px;width:.5px;height:44px;background:rgba(60,60,67,.3)"></div><div class="a cjk" style="left:0;top:80px;width:135px;height:44px;line-height:44px;text-align:center;font:400 17px 'Noto Sans CJK SC';color:#007aff">取消</div><div class="a cjk" style="left:135px;top:80px;width:135px;height:44px;line-height:44px;text-align:center;font:600 17px 'Noto Sans CJK SC';color:#007aff;${pr?'background:rgba(0,0,0,.08);border-radius:0 0 14px 0':''}">呼叫</div></div>`;}
 return `<div class="L" style="background:#fff">${map}${notice}${eta}${safety}${nav}${sheet}${alert}${homeBar('#111')}</div>`;
}
// ---------- iOS phone call ----------
function callView(t){
 const c=F.call;const on=t>=c.connect;const el=Math.max(0,Math.floor(t-c.connect));
 const top=on?`${pad(Math.floor(el/60))}:${pad(el%60)}`:'正在呼叫…';
 const spkOn=t>=c.spk;const spkPr=t>=c.spk-0.12&&t<c.spk+0.1;
 const ic={
  spk:col=>`<svg width="30" height="26" viewBox="0 0 30 26"><path d="M3 9h5l7-6v20l-7-6H3z" fill="${col}"/><path d="M19 8.5a6 6 0 0 1 0 9M22.5 5a11 11 0 0 1 0 16" stroke="${col}" stroke-width="2.2" fill="none" stroke-linecap="round"/></svg>`,
  ft:col=>`<svg width="32" height="22" viewBox="0 0 32 22"><rect x="1" y="2" width="21" height="18" rx="4" fill="${col}"/><path d="M23.5 8.5 31 4v14l-7.5-4.5z" fill="${col}"/><text x="11.5" y="15.5" text-anchor="middle" font-family="InterV" font-weight="700" font-size="11" fill="#5d6067">?</text></svg>`,
  mute:col=>`<svg width="24" height="30" viewBox="0 0 24 30"><rect x="7" y="2" width="10" height="17" rx="5" fill="${col}"/><path d="M3 14a9 9 0 0 0 18 0M12 23v5M3 2l18 24" stroke="${col}" stroke-width="2.2" fill="none" stroke-linecap="round"/></svg>`,
  add:col=>`<svg width="28" height="28" viewBox="0 0 28 28"><circle cx="15" cy="10" r="5.4" fill="none" stroke="${col}" stroke-width="2.2"/><path d="M6 25c1-5 4.6-7.6 9-7.6s8 2.6 9 7.6" fill="none" stroke="${col}" stroke-width="2.2"/><path d="M5 6v8M1 10h8" stroke="${col}" stroke-width="2.2" stroke-linecap="round"/></svg>`,
  pad:col=>`<svg width="26" height="30" viewBox="0 0 26 30">${[0,1,2,3].map(r=>[0,1,2].map(q=>(r===3&&q!==1)?'':`<circle cx="${4+q*9}" cy="${3+r*8}" r="3" fill="${col}"/>`).join('')).join('')}</svg>`};
 const btn=(x,y,bg,icon,l)=>`<div class="a" style="left:${x-38}px;top:${y-38}px;width:76px;height:76px;border-radius:38px;background:${bg};display:flex;align-items:center;justify-content:center">${icon}</div><div class="a cjk" style="left:${x-50}px;top:${y+45}px;width:100px;text-align:center;font:400 13px 'Noto Sans CJK SC','InterV';color:#fff">${l}</div>`;
 const r1=H-262,r2=H-140;const g='rgba(255,255,255,.22)';
 return `<div class="L" style="background:linear-gradient(170deg,#6f737a,#4a4d53 55%,#3a3d42)">
 <svg class="a" style="right:22px;top:62px" width="22" height="22" viewBox="0 0 22 22"><circle cx="11" cy="11" r="9.6" fill="none" stroke="rgba(255,255,255,.75)" stroke-width="1.5"/><path d="M11 9.6v5.6" stroke="rgba(255,255,255,.75)" stroke-width="1.8" stroke-linecap="round"/><circle cx="11" cy="6.6" r="1.1" fill="rgba(255,255,255,.75)"/></svg>
 <div class="a cjk" style="left:0;width:393px;top:112px;text-align:center;font:400 17px 'InterV','Noto Sans CJK SC';color:rgba(255,255,255,.62)">${top}</div>
 <div class="a" style="left:0;width:393px;top:138px;text-align:center;font:600 31px InterV;color:#fff;letter-spacing:.2px">170 3291 0371</div>
 ${btn(84,r1,spkOn?'#fff':(spkPr?'rgba(255,255,255,.4)':g),ic.spk(spkOn?'#3c3f45':'#fff'),'扬声器')}${btn(196.5,r1,g,ic.ft('#fff'),'FaceTime')}${btn(309,r1,g,ic.mute('#fff'),'静音')}
 ${btn(84,r2,g,ic.add('#fff'),'添加')}${btn(196.5,r2,g,ic.pad('#fff'),'拨号键盘')}${btn(309,r2,'#ff3b30',G.handset('#fff',135,34),'结束')}${homeBar()}</div>`;
}
// ---------- composition ----------
function viewFor(spec,t){switch(spec.type){case 'chat':return chatView(spec.chat,t);case 'car':return carView(spec,t);case 'mp':return mpView(t);case 'call':return callView(t);}return '';}
function wrap(html,style){return `<div class="L" style="${style}">${html}</div>`;}
function lockSegBefore(seg){const i=F.segments.indexOf(seg);for(let j=i-1;j>=0;j--)if(F.segments[j].type==='lock')return F.segments[j];return null;}
function postFix(){
 for(const el of root.querySelectorAll('[data-scroll]')){const v=el.getAttribute('data-scroll');if(!v)continue;const sc=JSON.parse(v);const row=el.querySelector(`[data-mid="${sc.mid}"]`);const box=el.parentElement;if(!row||!box)continue;
  const br=box.getBoundingClientRect(),rr=row.getBoundingClientRect();const target=br.height*0.42-((rr.top-br.top)+rr.height/2);el.style.transform=`translateY(${Math.max(0,target)*sc.p}px)`;}
 for(const el of root.querySelectorAll('[data-imgfx]')){const o=JSON.parse(el.getAttribute('data-imgfx'));const im=root.querySelector('#'+o.id);let a={x:63,y:H-SAFE-56-16-176,w:132,h:176};if(im){const r=im.getBoundingClientRect();a={x:r.left,y:r.top,w:r.width,h:r.height};}
  const b=IMG_FULL,q=o.q;el.style.left=lerp(a.x,b.x,q)+'px';el.style.top=lerp(a.y,b.y,q)+'px';el.style.width=lerp(a.w,b.w,q)+'px';el.style.height=lerp(a.h,b.h,q)+'px';}
}
function endCard(t){return `<div class="L" style="background:#000;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:${prog(t,F.cardAt,F.cardAt+0.6)}"><div class="cjk" style="font:400 30px 'Noto Sans CJK SC';letter-spacing:8px;color:#d8d8d8;margin-left:8px">我们到了</div><div class="cjk" style="margin-top:22px;font:400 13px 'Noto Sans CJK SC';color:#6f6f6f">虚构演绎 · 人物与聊天记录均为虚构</div></div>`;}
window.setTime=function(t){
 if(t>=F.blackAt){root.innerHTML=t<F.cardAt?'':endCard(t);return;}
 const seg=F.segments.find(s=>t>=s.s&&t<s.e)||F.segments[F.segments.length-1];const lp=prog(t,seg.s,seg.e);let body='',sm='normal';
 switch(seg.type){
  case 'lock':body=lockView(t,seg);sm='lock';break;
  case 'black':body='';sm='none';break;
  case 'sleep':body=wrap(viewFor(seg.from,seg.s-0.001),`opacity:${1-lp}`);sm=lp>.3?'none':'normal';break;
  case 'notifOpen':{const p=eio(lp);const ls=lockSegBefore(seg);const r={x:10,y:cardTop(0,ls.notifs.length),w:373,h:68};const x=lerp(r.x,0,p),y=lerp(r.y,0,p),w=lerp(r.w,W,p),h=lerp(r.h,H,p);
   body=wrap(lockView(seg.s-0.001,ls),`transform:scale(${lerp(1,1.06,p)});opacity:${1-p*.8}`)+`<div class="a" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-radius:${lerp(22,0,p)}px;overflow:hidden;background:#000"><div style="transform:scale(${w/W},${h/H});transform-origin:0 0;width:393px;height:${H}px;position:relative;opacity:${prog(lp,.15,.6)}">${viewFor(seg.to,t)}</div></div>`;sm=p<.5?'lock':(seg.to.type==='mp'?'dark':'normal');break;}
  case 'appSwitch':{const p=eio(lp);const s=lerp(1,.9,Math.sin(Math.PI*p));const gap=14;
   body=`<div class="L" style="background:#000"></div>`+wrap(viewFor(seg.from,seg.s-0.001),`transform:translateX(${(W+gap)*p}px) scale(${s});border-radius:${p>0&&p<1?38:0}px`)+wrap(viewFor(seg.to,t),`transform:translateX(${-(W+gap)*(1-p)}px) scale(${s});border-radius:${p>0&&p<1?38:0}px`);break;}
  case 'chat':body=chatView(seg.chat,t);break;
  case 'car':body=carView({page:seg.page,src:seg.src,shot:seg.shot,n:seg.n},t);break;
  case 'mp':body=mpView(t);sm='dark';break;
  case 'mpOpen':{const p=eio(lp);body=viewFor(seg.from,seg.s-0.001)+`<div class="L" style="background:rgba(0,0,0,${0.3*p})"></div>`+wrap(mpView(t),`transform:translateY(${(1-p)*H}px)`);sm=p>.5?'dark':'normal';break;}
  case 'callIn':{const p=eo(lp);body=mpView(seg.s-0.001)+wrap(callView(t),`opacity:${p};transform:scale(${lerp(1.08,1,p)})`);sm=p>.5?'normal':'dark';break;}
  case 'call':body=callView(t);break;
  case 'pop':case 'push':{const p=eio(lp);const back=seg.type==='pop';const under=back?viewFor(seg.to,t):viewFor(seg.from,seg.s-0.001),over=back?viewFor(seg.from,seg.s-0.001):viewFor(seg.to,t);const q=back?1-p:p;
   body=wrap(under,`transform:translateX(${-W*0.3*q}px)`)+`<div class="L" style="background:rgba(0,0,0,${0.25*q})"></div>`+wrap(over,`transform:translateX(${W*(1-q)}px);box-shadow:-6px 0 18px rgba(0,0,0,.35)`);break;}
  case 'imgOpen':body=imgTransition(t,seg,true,chatView('zhou',seg.s-0.001));sm=lp>.5?'none':'normal';break;
  case 'imgView':body=imgViewer(t,seg);sm='none';break;
  case 'imgClose':body=imgTransition(t,seg,false,chatView('zhou',t));sm=lp<.5?'none':'normal';break;
 }
 root.innerHTML=body+`<div class="L" style="pointer-events:none;z-index:60;opacity:${sm==='none'?0:1}">${statusBar(t,sm==='lock'?'lock':sm==='dark'?'dark':'normal')}</div>`+bannerHtml(t)+(sm==='none'&&seg.type==='black'?'':island(t));
 postFix();
};
window.setTime(0);
})();
</script></body></html>
