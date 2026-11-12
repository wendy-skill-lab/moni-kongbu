// ===================== 《已就寝》 modules (appended after film_head.html) =====================
const VT=98, VH=221;
const IRN=(t,op)=>`<img src="${A}noise/n${pad(Math.floor(t*15)%12)}.png" class="a" style="left:0;top:0;width:100%;height:100%;mix-blend-mode:overlay;opacity:${op*((F.kb&&F.kb.noise!=null)?F.kb.noise:1)}">`;
function wrap(html,style){return `<div class="L" style="${style}">${html}</div>`;}
function lockSegBefore(seg){const i=F.segments.indexOf(seg);for(let j=i-1;j>=0;j--)if(F.segments[j].type==='lock')return F.segments[j];return null;}
const fmtSec=s=>pad(Math.floor(s/3600)%24)+':'+pad(Math.floor(s/60)%60)+':'+pad(s%60);
const tapped=(what,t,a=0.12,b=0.12)=>(F.taps||[]).some(x=>x.what===what&&t>=x.t-a&&t<x.t+b);
function spin(t,s=24,c='#fff'){const k=Math.floor(t*12)%12;let p='';for(let i=0;i<12;i++){const o=0.18+0.82*(((k-i+12)%12)===0?1:Math.max(0,1-((k-i+12)%12)/9));p+=`<rect x="11" y="1.5" width="2" height="6" rx="1" fill="${c}" opacity="${o.toFixed(2)}" transform="rotate(${i*30} 12 12)"/>`;}return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" style="display:block">${p}</svg>`;}
// ---------- typing with pauses (chunk[2] = seconds to wait before this chunk; pauses are not compressed) ----------
function draftState(d,t){
 let nat=0,events=[];
 for(const c of d.chunks){const [py,txt,pause]=c;const pz=pause||0;
  if(py){const letters=py.replace(/ /g,'');for(let i=0;i<letters.length;i++){events.push({n:nat,pz,type:'k',ch:letters[i]});nat+=0.105;}nat+=0.12;events.push({n:nat,pz,type:'c',txt,py});nat+=0.2;}
  else{nat+=0.2;events.push({n:nat,pz,type:'c',txt,py});nat+=0.14;}}
 let acc=0;const pzs=[];for(const c of d.chunks){acc+=(c[2]||0);pzs.push(acc);}
 const totalP=acc;const avail=(d.send-0.25)-d.start-totalP,f=d.rate||Math.min(1,avail/nat);
 let ci=0;for(const e of events){e.t=d.start+e.n*f+pzs[ci];if(e.type==='c')ci++;}
 let committed='',chunkIdx=0,typedInChunk=0,pressed=null;
 const syl=d.chunks.map(c=>c[0]?c[0].split(' '):[]);
 for(const e of events){if(e.t>t)break;if(e.type==='k'){typedInChunk++;if(t-e.t<0.09)pressed=e.ch;}else{committed+=e.txt;chunkIdx++;typedInChunk=0;}}
 let marked='';
 if(chunkIdx<d.chunks.length&&typedInChunk>0){let n=typedInChunk;const s=syl[chunkIdx];const parts=[];for(const x of s){if(n<=0)break;parts.push(x.slice(0,n));n-=x.length;}marked=parts.join("'");}
 const target=chunkIdx<d.chunks.length?d.chunks[chunkIdx][1]:'';
 const cands=marked?(F.decoys[target]||[target]):null;
 return {committed,marked,cands,pressed,sendPress:!d.hold&&t>d.send-0.1&&t<d.send};
}
// ---------- unread ----------
function seenUntil(chat,t){let v=F.chats[chat].readUntil;for(const s of F.segments){if(s.s>t)break;const here=(s.type==='chat'&&s.chat===chat)||(s.type==='svc'&&chat==='school');if(here)v=Math.max(v,Math.min(s.e,t));}return v;}
function itemsOf(chat){return chat==='school'?F.svc:F.msgs[chat];}
function unreadOf(chat,t){const seen=seenUntil(chat,t);return itemsOf(chat).filter(m=>m.kind!=='time'&&m.who!=='me'&&m.t<=t&&m.t>seen).length;}
function otherUnread(chat,t){return Object.keys(F.chats).filter(c=>c!==chat).map(c=>unreadOf(c,t)).reduce((a,b)=>a+b,0);}
function navBar(title,t,cur,right){const oc=otherUnread(cur,t);
 return `<div class="a" style="left:0;top:0;width:393px;height:98px;background:#1e1e1e"><div class="a" style="left:13px;top:65px">${G.back()}</div>${oc?`<div class="a" style="left:31px;top:62px;font:400 17px InterV;color:#ededed">${oc}</div>`:''}<div class="a cjk" style="left:60px;width:273px;top:62px;text-align:center;font:500 17px 'Noto Sans CJK SC';color:#ededed;white-space:nowrap">${title}</div>${right||`<div class="a" style="right:14px;top:73px">${G.more}</div>`}</div>`;}
// ---------- @ picker ----------
function atSheet(chat,t){const s=(F.atPick||[]).find(x=>x.chat===chat&&t>=x.s&&t<x.e+0.3);if(!s)return '';
 const p=Math.min(eo(prog(t,s.s,s.s+0.32)),1-eio(prog(t,s.e,s.e+0.28)));
 const rows=[['wang','王老师'],['p1','张子轩妈妈'],['p2','李一诺爸爸'],['p3','刘思雨妈妈'],['p4','赵晨阳妈妈'],['p5','王浩然妈妈'],['p6','陈雨桐爸爸'],['p7','孙一鸣妈妈'],['p8','周佳怡妈妈'],['p9','林子墨妈妈'],['p10','黄梓涵妈妈'],['p11','吴俊杰爸爸'],['p12','郑欣怡妈妈'],['p13','何宇航妈妈'],['p14','马诗琪妈妈'],['p15','胡嘉豪爸爸']];
 const pr=t>=s.tapAt-0.12&&t<s.e;
 const list=rows.map((r,i)=>`<div class="a" style="left:0;top:${170+i*60}px;width:393px;height:60px;${i===0&&pr?'background:#2a2a2a':''}"><img src="${avOf(r[0])}" class="a" style="left:16px;top:10px;width:40px;height:40px;border-radius:5px;object-fit:cover"><div class="a cjk" style="left:70px;top:18px;font:400 17px 'Noto Sans CJK SC';color:#e6e6e6">${r[1]}</div><div class="a" style="left:70px;right:0;bottom:0;height:.5px;background:#262626"></div></div>`).join('');
 return `<div class="L" style="background:rgba(0,0,0,${0.4*p});z-index:32"></div><div class="L" style="top:${(1-p)*H}px;background:#111;z-index:33;overflow:hidden">
 <div class="a cjk" style="left:16px;top:62px;font:400 17px 'Noto Sans CJK SC';color:#e6e6e6">取消</div><div class="a cjk" style="left:0;width:393px;top:62px;text-align:center;font:500 17px 'Noto Sans CJK SC';color:#ededed">选择提醒的人</div>
 <div class="a cjk" style="left:12px;top:104px;width:369px;height:36px;border-radius:7px;background:#262626;display:flex;align-items:center;justify-content:center;gap:6px;font:400 16px 'Noto Sans CJK SC';color:#7a7a7a"><svg width="15" height="15" viewBox="0 0 15 15"><circle cx="6.4" cy="6.4" r="4.9" fill="none" stroke="#7a7a7a" stroke-width="1.5"/><path d="M10 10l3.6 3.6" stroke="#7a7a7a" stroke-width="1.5" stroke-linecap="round"/></svg>搜索</div>
 <div class="a cjk" style="left:16px;top:150px;font:400 13px 'Noto Sans CJK SC';color:#777">群成员</div>${list}</div>`;}
// ---------- WeChat chat (with back-button unread count and @ picker) ----------
const _mc=document.createElement('canvas').getContext('2d');
function fieldLines(str,w){_mc.font="400 17px 'Noto Sans CJK SC'";let n=1,x=0;for(const ch of str){const cw=ch==='|'?3:_mc.measureText(ch).width;if(x+cw>w+0.5){n++;x=cw;}else x+=cw;}return n;}
function chatView(chat,t){
 const msgs=F.msgs[chat].filter(m=>m.t<=t);
 const kb=winP(F.keyboard,chat,t);const pp=winP(F.plus,chat,t);
 const d=activeDraft(chat,t);const ds=d?draftState(d,t):null;
 const lower=Math.max(kb*KBH,pp*PNH);const safe=lerp(SAFE,0,clamp(lower/60,0,1));
 const typingNow=F.typing.some(w=>w.chat===chat&&t>=w.s&&t<w.e);
 const title=typingNow?'对方正在输入...':F.chats[chat].title;
 const text=ds?ds.committed:'';const marked=ds?ds.marked:'';
 const focused=kb>0.5;
 const caretOn=focused&&(ds&&ds.marked?false:(Math.floor(t*1.9)%2===0||(ds&&t-d.start>-0.2)));
 const nl=fieldLines(text+marked+(caretOn?'|':''),243);const ex=(Math.min(nl,4)-1)*22;
 const barTop=H-lower-safe-56-ex;
 const field=`<div class="a cjk" style="left:50px;top:9px;width:${393-50-82}px;height:${38+ex}px;border-radius:5px;background:#2c2c2c;overflow:hidden;font:400 17px/22px 'Noto Sans CJK SC';color:#e8e8e8"><div class="a" style="left:9px;right:9px;bottom:8px;white-space:pre-wrap;word-break:break-all;line-break:anywhere">${text}${marked?`<span style="text-decoration:underline;text-decoration-color:#9a9a9a;text-underline-offset:4px;color:#e8e8e8">${marked}</span>`:''}${caretOn?`<span style="display:inline-block;width:2px;height:21px;background:#3eb575;margin-left:1px;border-radius:1px;vertical-align:-4px"></span>`:''}</div></div>`;
 const bar=`<div class="a" style="left:0;top:${barTop}px;width:393px;height:${56+ex+safe+lower+2}px;background:#1e1e1e;border-top:.5px solid #2a2a2a"><div class="a" style="left:10px;top:${13+ex}px">${G.voice}</div>${field}<div class="a" style="right:48px;top:${13+ex}px">${G.emoji}</div><div class="a" style="right:10px;top:${13+ex}px;${tapped('plusBtn',t,0.1,0.18)?'opacity:.5':''}">${G.plus}</div></div>`;
 const kbd=kb>0?`<div class="a" style="left:0;top:${H-kb*KBH}px;width:393px;height:${KBH}px">${keyboard(ds,t)}</div>`:'';
 const pnl=pp>0?`<div class="a" style="left:0;top:${H-pp*PNH}px;width:393px;height:${PNH}px">${plusPanel(t,F.plus.find(w=>w.chat===chat&&t>=w.s&&t<w.e+0.3))}</div>`:'';
 const sc=scrollP(chat,t);
 const list=`<div class="a" data-list="1" style="left:0;top:98px;width:393px;height:${barTop-98}px;overflow:hidden;display:flex;flex-direction:column;justify-content:flex-end;padding-bottom:16px"><div data-scroll='${sc.mid&&sc.p>0?JSON.stringify(sc):''}' style="display:flex;flex-direction:column;gap:17px">${msgs.map(m=>msgRow(m,t,chat)).join('')}</div></div>`;
 return `<div class="L" style="background:#111">${list}${bar}${kbd}${pnl}${navBar(title,t,chat)}${atSheet(chat,t)}${(F.sheet&&F.sheet.chat===chat)?sheetHtml(t):''}${homeBar()}</div>`;
}
// ---------- service account (公众号) ----------
function tplCard(m,t,last){
 const age=t-m.t;let anim='';if(age>=0&&age<0.26){const q=eo(age/0.26);anim=`opacity:${Math.min(1,q*1.6)};transform:translateY(${(1-q)*10}px)`;}
 const pr=last&&tapped('card',t,0.14,0.2);
 const fields=m.fields.map(([k,v])=>`<div style="display:flex;gap:10px;margin-top:7px"><div style="flex:0 0 66px;color:#8d8d8d">${k}</div><div style="color:${v.hl?'#e8e8e8':'#d4d4d4'};${v.hl?'font-weight:500':''}">${v.hl?v.v:v}</div></div>`).join('');
 return `<div style="margin:0 12px;border-radius:8px;background:${pr?'#2a2a2a':'#1f1f1f'};padding:15px 16px 0;${anim}" class="cjk">
  <div style="display:flex;justify-content:space-between;align-items:center"><div style="font:500 17px 'Noto Sans CJK SC';color:#e8e8e8">${m.title}</div><svg width="18" height="4" viewBox="0 0 18 4"><circle cx="2" cy="2" r="1.6" fill="#777"/><circle cx="9" cy="2" r="1.6" fill="#777"/><circle cx="16" cy="2" r="1.6" fill="#777"/></svg></div>
  <div style="font:400 14px 'Noto Sans CJK SC';color:#8d8d8d;margin-top:9px">${m.intro}</div>
  <div style="font:400 14.5px 'Noto Sans CJK SC';margin-top:4px">${fields}</div>
  <div style="margin-top:13px;border-top:.5px solid #2f2f2f;height:40px;display:flex;align-items:center;gap:7px"><img src="${TH}school_badge.jpg" style="width:16px;height:16px;border-radius:8px"><div style="font:400 13px 'Noto Sans CJK SC';color:#8d8d8d;flex:1">南城一中家校通</div><svg width="16" height="16" viewBox="0 0 16 16"><circle cx="5" cy="9" r="3" fill="none" stroke="#6f7fb0" stroke-width="1.4"/><circle cx="11" cy="7" r="3" fill="none" stroke="#6f7fb0" stroke-width="1.4"/></svg><div style="font:400 13px 'Noto Sans CJK SC';color:#8d8d8d">小程序</div><svg width="7" height="12" viewBox="0 0 7 12"><path d="M1 1l5 5-5 5" stroke="#666" stroke-width="1.4" fill="none"/></svg></div></div>`;}
function svcView(t){
 const items=F.svc.filter(m=>m.t<=t);const lastIdx=items.map(m=>m.kind).lastIndexOf('tpl');
 const mh=50;const barTop=H-SAFE-mh;
 const body=items.map((m,i)=>m.kind==='time'?`<div class="ts">${m.label||clock(m.t)}</div>`:tplCard(m,t,i===lastIdx)).join('');
 const list=`<div class="a" style="left:0;top:98px;width:393px;height:${barTop-98}px;overflow:hidden;display:flex;flex-direction:column;justify-content:flex-end;padding-bottom:14px"><div style="display:flex;flex-direction:column;gap:12px">${body}</div></div>`;
 const pr=tapped('menu',t,0.14,0.2);
 const menu=`<div class="a" style="left:0;top:${barTop}px;width:393px;height:${mh+SAFE}px;background:#1e1e1e;border-top:.5px solid #2a2a2a"><svg class="a" style="left:14px;top:13px" width="26" height="24" viewBox="0 0 26 24"><rect x="1" y="3" width="24" height="17" rx="3" fill="none" stroke="#bcbcbc" stroke-width="1.5"/><path d="M5 8h2M9 8h2M13 8h2M17 8h2M21 8h0M5 12h2M9 12h2M13 12h2M17 12h2M8 16h10" stroke="#bcbcbc" stroke-width="1.5" stroke-linecap="round"/></svg>
 <div class="a" style="left:52px;top:0;width:.5px;height:${mh}px;background:#2f2f2f"></div>
 ${['家校服务','看班','我的'].map((x,i)=>{const w=(393-52)/3;return `<div class="a cjk" style="left:${52+i*w}px;top:0;width:${w}px;height:${mh}px;line-height:${mh}px;text-align:center;font:400 15px 'Noto Sans CJK SC';color:#d8d8d8;${i===1&&pr?'background:#2c2c2c':''}">${i!==1?'<span style="font-size:11px;color:#8a8a8a;margin-right:4px">☰</span>':''}${x}</div>${i<2?`<div class="a" style="left:${52+(i+1)*w}px;top:14px;width:.5px;height:22px;background:#2f2f2f"></div>`:''}`;}).join('')}</div>`;
 const right=`<svg class="a" style="right:16px;top:64px" width="22" height="22" viewBox="0 0 22 22"><circle cx="11" cy="7.5" r="4.2" fill="none" stroke="#e6e6e6" stroke-width="1.5"/><path d="M3 20c.8-4.4 4-6.8 8-6.8s7.2 2.4 8 6.8" fill="none" stroke="#e6e6e6" stroke-width="1.5" stroke-linecap="round"/></svg>`;
 return `<div class="L" style="background:#111">${list}${menu}${navBar('南城一中家校通',t,'school',right)}${homeBar()}</div>`;
}
// ---------- chat list (with pull-down “最近使用” mini programs) ----------
function grpAvatar(size){const srcs=['avatar_wang','avatar_p1','avatar_p2','avatar_p3','avatar_mom','avatar_p4','school_badge','avatar_p2','avatar_p1'];const c=(size-6)/3;return `<div style="width:${size}px;height:${size}px;border-radius:5px;background:#3a3a3a;display:grid;grid-template-columns:repeat(3,${c}px);gap:1.5px;padding:1.5px">${srcs.map(s=>`<img src="${TH}${s}.jpg" style="width:${c}px;height:${c}px;object-fit:cover;display:block">`).join('')}</div>`;}
function ftAvatar(size){return `<div style="width:${size}px;height:${size}px;border-radius:5px;background:#2aae67;display:flex;align-items:center;justify-content:center"><svg width="${size*0.55}" height="${size*0.55}" viewBox="0 0 24 24"><path d="M3 6.5h7l2 2.2h9v10.8H3z" fill="none" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/><path d="M8.5 14h7M13 11.5l2.5 2.5-2.5 2.5" stroke="#fff" stroke-width="1.6" fill="none" stroke-linecap="round"/></svg></div>`;}
function subAvatar(size){return `<div style="width:${size}px;height:${size}px;border-radius:5px;background:#3b78d8;display:flex;align-items:center;justify-content:center"><svg width="${size*0.55}" height="${size*0.55}" viewBox="0 0 24 24"><rect x="4" y="3.5" width="16" height="17" rx="2" fill="none" stroke="#fff" stroke-width="1.8"/><path d="M8 8.5h8M8 12h8M8 15.5h5" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/></svg></div>`;}
function rowOf(chat,t){
 const ms=itemsOf(chat).filter(m=>m.kind!=='time'&&m.t<=t);const last=ms[ms.length-1];const c=F.chats[chat];
 const unread=unreadOf(chat,t);
 let preview;
 if(chat==='school')preview=`[${last.title}]`;
 else{const who=chat==='grp'&&last.who!=='me'?nameOf(last.who)+'：':'';preview=who+(last.kind==='voice'?'[语音]':last.text);}
 const at=chat==='grp'&&F.msgs.grp.some(m=>m.atMe&&m.t<=t&&m.t>seenUntil('grp',t));
 if(at)preview=`<span style="color:#e2574c">[有人@我]</span>`+preview;
 const av=chat==='grp'?grpAvatar(48):avatarImg(chat==='school'?TH+'school_badge.jpg':avOf(chat),48);
 return {name:c.title.replace(/\(\d+\)$/,''),av,unread,preview,time:last.t<0?last.when:clock(last.t),k:last.t};
}
function listView(t,seg){
 seg=seg||{};
 const rows=['school','grp','wang','chenmo'].map(c=>rowOf(c,t)).concat(F.listStatic.map(r=>({...r,av:r.icon==='ft'?ftAvatar(48):r.icon==='sub'?subAvatar(48):r.icon==='grid'?grpAvatar(48):avatarImg(TH+r.av+'.jpg',48),unread:0}))).sort((a,b)=>b.k-a.k);
 const tapRow=seg.tapRow;
 let html='';rows.forEach((r,i)=>{const y=150+i*72;const pr=tapRow&&r.name===tapRow[1]&&t>=tapRow[0]-0.12&&t<tapRow[0]+0.3;
  const badge=r.unread?`<div class="a" style="left:52px;top:4px;min-width:19px;height:19px;padding:0 5px;border-radius:10px;background:#fa5151;color:#fff;font:500 12px/19px InterV;text-align:center">${r.unread}</div>`:'';
  html+=`<div class="lrow" style="top:${y}px;${pr?'background:#262626':''}"><div class="a" style="left:16px;top:12px">${r.av}</div>${badge}<div class="a cjk" style="left:76px;top:13px;width:220px;font:400 17px 'Noto Sans CJK SC';color:#e3e3e3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${r.name}</div><div class="a" style="right:16px;top:16px;font:400 12px 'InterV','Noto Sans CJK SC';color:#6c6c6c">${r.time}</div><div class="a cjk" style="left:76px;top:41px;width:270px;font:400 14px 'Noto Sans CJK SC';color:#7c7c7c;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${r.preview}</div>${r.muted?'<svg class="a" style="right:16px;top:44px" width="15" height="15" viewBox="0 0 15 15"><path d="M7.5 1.5a4 4 0 0 0-4 4v3L2 10.5h11L11.5 8.5v-3a4 4 0 0 0-4-4zM6 12.5a1.6 1.6 0 0 0 3 0M1.5 1.5l12 12" stroke="#5c5c5c" stroke-width="1.3" fill="none" stroke-linecap="round"/></svg>':''}<div class="a" style="left:76px;right:0;bottom:0;height:.5px;background:#262626"></div></div>`;});
 const tab=(x,l,sel,ic)=>`<div class="a" style="left:${x-30}px;top:6px;width:60px;text-align:center">${ic}<div class="cjk" style="font:400 10.5px 'Noto Sans CJK SC';color:${sel?'#07c160':'#b0b0b0'};margin-top:2px">${l}</div></div>`;
 const icChat=`<svg width="28" height="26" viewBox="0 0 28 26"><path d="M14 2C7 2 2 6.4 2 11.8c0 3 1.6 5.6 4.1 7.4L5 23.4l4.8-2.6c1.3.4 2.7.6 4.2.6 7 0 12-4.4 12-9.7S21 2 14 2z" fill="#07c160"/><circle cx="9.4" cy="11.6" r="1.6" fill="#181818"/><circle cx="14" cy="11.6" r="1.6" fill="#181818"/><circle cx="18.6" cy="11.6" r="1.6" fill="#181818"/></svg>`;
 const icContacts=`<svg width="28" height="26" viewBox="0 0 28 26"><circle cx="13" cy="8.5" r="5.2" fill="none" stroke="#b0b0b0" stroke-width="1.6"/><path d="M3.5 23c.8-5 4.6-7.8 9.5-7.8s8.7 2.8 9.5 7.8z" fill="none" stroke="#b0b0b0" stroke-width="1.6" stroke-linejoin="round"/></svg>`;
 const icDisc=`<svg width="28" height="26" viewBox="0 0 28 26"><circle cx="14" cy="13" r="10.6" fill="none" stroke="#b0b0b0" stroke-width="1.6"/><path d="M18.6 8.4 16 15.4 9.4 17.6 12 10.6z" fill="none" stroke="#b0b0b0" stroke-width="1.5" stroke-linejoin="round"/></svg>`;
 const icMe=`<svg width="28" height="26" viewBox="0 0 28 26"><circle cx="14" cy="9" r="5.4" fill="none" stroke="#b0b0b0" stroke-width="1.6"/><path d="M4 24c1-5.6 5-8.6 10-8.6s9 3 10 8.6" fill="none" stroke="#b0b0b0" stroke-width="1.6" stroke-linecap="round"/></svg>`;
 const total=Object.keys(F.chats).map(c=>unreadOf(c,t)).reduce((a,b)=>a+b,0);
 const tabs=`<div class="a" style="left:0;top:${H-49-SAFE}px;width:393px;height:${49+SAFE}px;background:#191919;border-top:.5px solid #262626">${tab(49,'微信',true,icChat)}${total?`<div class="a" style="left:58px;top:2px;min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:#fa5151;color:#fff;font:500 11.5px/18px InterV;text-align:center">${total}</div>`:''}${tab(147,'通讯录',false,icContacts)}${tab(246,'发现',false,icDisc)}${tab(344,'我',false,icMe)}</div>`;
 const head=`<div class="a cjk" style="left:0;top:62px;width:393px;text-align:center;font:500 17px 'Noto Sans CJK SC';color:#ededed">微信${total?`(${total})`:''}</div><svg class="a" style="right:16px;top:62px" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10.4" fill="none" stroke="#e6e6e6" stroke-width="1.5"/><path d="M12 7v10M7 12h10" stroke="#e6e6e6" stroke-width="1.5" stroke-linecap="round"/></svg><div class="a cjk" style="left:12px;top:104px;width:369px;height:36px;border-radius:7px;background:#262626;display:flex;align-items:center;justify-content:center;gap:6px;font:400 16px 'Noto Sans CJK SC';color:#7a7a7a"><svg width="15" height="15" viewBox="0 0 15 15"><circle cx="6.4" cy="6.4" r="4.9" fill="none" stroke="#7a7a7a" stroke-width="1.5"/><path d="M10 10l3.6 3.6" stroke="#7a7a7a" stroke-width="1.5" stroke-linecap="round"/></svg>搜索</div>`;
 // pull-down panel
 let pull=0,panel='';
 if(seg.pull){pull=eo(prog(t,seg.pull,seg.pull+0.42));}
 if(pull>0){const PH=300;const icPr=t>=seg.pullTap-0.12&&t<seg.pullTap+0.4;
  const mp=[['school','南城一中家校通'],['park','停车缴费'],['med','电子医保'],['shop','社区团购']];
  const ic=k=>k==='school'?`<img src="${TH}school_badge.jpg" style="width:52px;height:52px;border-radius:26px;display:block">`:`<div style="width:52px;height:52px;border-radius:26px;background:${k==='park'?'#2f6fe0':k==='med'?'#1aa36b':'#f08a24'};display:flex;align-items:center;justify-content:center;font:600 20px InterV;color:#fff">${k==='park'?'P':k==='med'?'+':'团'}</div>`;
  panel=`<div class="a" style="left:0;top:0;width:393px;height:${98+PH*pull}px;background:linear-gradient(#26262a,#1a1a1d);overflow:hidden;z-index:2"><div class="a cjk" style="left:0;width:393px;top:${62+ (1-pull)*-40}px;text-align:center;font:500 17px 'Noto Sans CJK SC';color:#ededed;opacity:${pull}">最近</div><div class="a" style="left:0;top:${110+(1-pull)*-60}px;width:393px;opacity:${pull}"><div class="a cjk" style="left:22px;top:0;font:400 13px 'Noto Sans CJK SC';color:#8a8a8a">最近使用</div>${mp.map((m,i)=>`<div class="a" style="left:${22+i*92}px;top:30px;width:64px;text-align:center;${i===0&&icPr?'opacity:.55':''}"><div style="margin:0 6px">${ic(m[0])}</div><div class="cjk" style="font:400 11.5px 'Noto Sans CJK SC';color:#cfcfcf;margin-top:7px;white-space:nowrap;margin-left:-14px;width:92px">${m[1]}</div></div>`).join('')}<div class="a cjk" style="left:22px;top:140px;font:400 13px 'Noto Sans CJK SC';color:#8a8a8a">我的小程序</div>${[0,1,2,3].map(i=>`<div class="a" style="left:${28+i*92}px;top:170px;width:52px;height:52px;border-radius:26px;background:#2f2f33"></div>`).join('')}</div></div>`;}
 const shift=pull*300;
 return `<div class="L" style="background:#111">${panel}<div class="L" style="transform:translateY(${shift}px)">${head}${html}</div>${tabs}${homeBar()}</div>`;
}
// ---------- 看班 (live classroom camera, mini program) ----------
function liveAt(t){
 const o=(F.kb.over||[]).find(x=>t>=x.s&&t<x.e);
 if(o){if(o.kind==='connect')return {kind:'connect'};if(o.kind==='buffer')return {kind:'buffer',img:o.img.startsWith('c')?`${A}frames/${o.img}.jpg`:`${TH}kb_${o.img}.jpg`,ts:o.ts,ir:!!o.ir,msg:o.msg};}
 const L=F.kb.live;let e=L[0];for(const x of L){if(t>=x.s)e=x;else break;}
 if(e.kind==='clip'){const n=F.kb.clips[e.clip];let i=Math.floor((e.from+(t-e.s)*(e.rate||1))*24);i=clamp(i,0,n-1);return {kind:'ok',img:`${A}frames/${e.clip}/f${String(i+1).padStart(3,'0')}.jpg`,ts:clockSec(t),ir:!!e.ir};}
 if(e.kind==='still'){const r={kind:'ok',img:`${TH}kb_${e.src}.jpg`,ts:clockSec(t),ir:!!e.ir,glow:e.glow?sio(prog(t,e.glow[0],e.glow[1])):0,jolt:e.jolt&&t>=e.jolt[0]&&t<e.jolt[1]};if(e.pulse){const P=e.pulse;let a=0;if(t>=P.s){a=(P.steady!=null&&t>=P.steady)?P.hold:(P.lo+(P.hi-P.lo)*(P.on?(()=>{const ph=(((t-P.s)%P.period)+P.period)%P.period/P.period;return clamp((ph-P.on[0])/0.035,0,1)*clamp((P.on[1]-ph)/0.06,0,1);})():(0.5-0.5*Math.cos(2*Math.PI*(t-P.s)/P.period))));a*=clamp((t-P.s)/0.3,0,1);}r.img2=`${TH}kb_${P.src}.jpg`;r.a2=a;}return r;}
 return {kind:e.kind,ts:clockSec(t)};
}
function countAt(t){let c=F.kb.counts[0][1];for(const x of F.kb.counts)if(t>=x[0])c=x[1];return c;}
function zoomAt(t){let z=1,cx=.5,cy=.5;for(const q of F.kb.zooms){if(t<q.s||t>q.e)continue;const p=eo(prog(t,q.s,q.s+0.6))*(1-eio(prog(t,q.e-0.5,q.e)));z=lerp(1,q.z,p);const hx=0.5/z,hy=0.5/z;cx=lerp(.5,clamp(q.fx,hx,1-hx),p);cy=lerp(.5,clamp(q.fy,hy,1-hy),p);}return {z,cx,cy};}
function osd(ts,z){return `<div class="a" style="left:${7*z}px;top:${6*z}px;font:600 ${9.4*z}px 'DejaVu Sans Mono','Noto Sans CJK SC',monospace;color:#fff;text-shadow:0 0 ${1.2*z}px #000,0 0 ${1.2*z}px #000;letter-spacing:${0.2*z}px;white-space:nowrap">2026-11-09 星期一 ${fmtSec(ts)}</div><div class="a cjk" style="right:${8*z}px;bottom:${6*z}px;font:600 ${9.6*z}px 'Noto Sans CJK SC';color:#fff;text-shadow:0 0 ${1.2*z}px #000,0 0 ${1.2*z}px #000">高一(7)班${CAMN===2?' 机位2':''}</div>`;}
function watermark(){let s='';for(let r=0;r<3;r++)for(let c=0;c<3;c++)s+=`<div class="a cjk" style="left:${-30+c*150+(r%2)*60}px;top:${18+r*72}px;transform:rotate(-18deg);font:400 11px 'Noto Sans CJK SC';color:rgba(255,255,255,.075);white-space:nowrap">陈默妈妈 138****6271</div>`;return s;}
function videoBox(t,v,count,zoom){
 let inner='';
 if(v.kind==='offline'){inner=`<div class="a" style="inset:0;background:#0c0c0c;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px"><svg width="34" height="30" viewBox="0 0 34 30"><rect x="3" y="7" width="20" height="16" rx="3" fill="none" stroke="#8a8a8a" stroke-width="1.8"/><path d="M23 13l8-4.5v13L23 17" fill="none" stroke="#8a8a8a" stroke-width="1.8" stroke-linejoin="round"/><path d="M4 3l26 24" stroke="#8a8a8a" stroke-width="1.8" stroke-linecap="round"/></svg><div class="cjk" style="font:500 14px 'Noto Sans CJK SC';color:#d0d0d0">设备离线</div><div class="cjk" style="font:400 11px 'Noto Sans CJK SC';color:#7d7d7d">请检查设备网络后重试</div><div class="cjk" style="margin-top:4px;padding:4px 14px;border:1px solid #555;border-radius:14px;font:400 12px 'Noto Sans CJK SC';color:#cfcfcf">重新连接</div></div>`;}
 else if(v.kind==='connect'){inner=`<div class="a" style="inset:0;background:#000;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:9px">${spin(t,24)}<div class="cjk" style="font:400 11.5px 'Noto Sans CJK SC';color:#9a9a9a">正在连接设备…</div></div>`;}
 else{const z=zoom||{z:1,cx:.5,cy:.5};const w2=393*z.z,h2=VH*z.z,l=393/2-z.cx*w2,tp=VH/2-z.cy*h2;
  inner=`<div class="a" style="left:${l}px;top:${tp}px;width:${w2}px;height:${h2}px;${v.jolt?'transform:translate(-3px,7px) scale(1.02);filter:brightness(1.35)':''}"><img src="${v.img}" style="width:100%;height:100%;object-fit:cover;display:block;${v.ir?'filter:grayscale(1) contrast(1.06) brightness(.97)':'filter:saturate(.92) contrast(1.02)'}">${v.img2?`<img src="${v.img2}" style="position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;display:block;opacity:${(v.a2||0).toFixed(3)};${v.ir?'filter:grayscale(1) contrast(1.06) brightness(.97)':''}">`:''}${v.kind==='ok'?detHtml(t,z.z):''}${osd(v.ts,z.z)}</div>${IRN(v.kind==='buffer'?0.3:t,v.ir?0.2+0.12*(v.glow||0):0.07)}${v.glow?`<div class="a" style="inset:0;background:linear-gradient(to top,rgba(255,255,255,${(0.92*v.glow).toFixed(3)}) 0%,rgba(255,255,255,${(0.55*v.glow).toFixed(3)}) 22%,rgba(255,255,255,${(0.12*v.glow).toFixed(3)}) 48%,rgba(255,255,255,0) 64%)"></div>`:''}`;
  if(v.kind==='buffer')inner+=`<div class="a" style="inset:0;background:rgba(0,0,0,.28);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px">${spin(t,24)}<div class="cjk" style="font:400 11.5px 'Noto Sans CJK SC';color:#e0e0e0;text-shadow:0 0 3px #000">${v.msg||'加载中…'}</div></div>`;
  if(z.z>1.05)inner+=`<div class="a" style="left:${393/2-22}px;top:8px;width:44px;height:20px;border-radius:10px;background:rgba(0,0,0,.5);font:600 11px/20px InterV;color:#fff;text-align:center;opacity:${clamp((z.z-1.05)*4,0,1)}">${z.z.toFixed(1)}x</div>`;
  if(count)inner+=`<div class="a cjk" style="left:7px;bottom:6px;padding:1px 5px;border-radius:3px;background:rgba(0,0,0,.42);font:400 9.4px 'Noto Sans CJK SC';color:rgba(255,255,255,.86)">AI 在室学生 ${count}</div>`;}
 return `<div class="a" style="left:0;top:${VT}px;width:393px;height:${VH}px;overflow:hidden;background:#000">${inner}${watermark()}</div>`;
}
function kbIcons(c='#d6d6d6',on=false,pr=false){return `<svg width="22" height="20" viewBox="0 0 22 20" style="${pr?'opacity:.4':''}"><path d="M2 7h4l5-4v14l-5-4H2z" fill="none" stroke="${c}" stroke-width="1.6" stroke-linejoin="round"/>${on?`<path d="M14.6 7.3a3.9 3.9 0 0 1 0 5.4M17.3 4.9a7.3 7.3 0 0 1 0 10.2" fill="none" stroke="${c}" stroke-width="1.6" stroke-linecap="round"/>`:`<path d="M15 7l5 5M20 7l-5 5" stroke="${c}" stroke-width="1.6" stroke-linecap="round"/>`}</svg><svg width="22" height="20" viewBox="0 0 22 20"><path d="M2 6h4.5L8.3 3.5h5.4L15.5 6H20v11H2z" fill="none" stroke="${c}" stroke-width="1.6" stroke-linejoin="round"/><circle cx="11" cy="11.3" r="3.2" fill="none" stroke="${c}" stroke-width="1.6"/></svg><svg width="20" height="20" viewBox="0 0 20 20"><path d="M2.5 7V2.5H7M13 2.5h4.5V7M17.5 13v4.5H13M7 17.5H2.5V13" fill="none" stroke="${c}" stroke-width="1.7" stroke-linecap="round"/></svg>`;}
function replayZoom(t){const P=F.kb.replay.zpath;if(!P||!P.length)return {z:1,cx:.5,cy:.5};let a=P[0],b=P[0];
 if(t<=P[0][0])a=b=P[0];else if(t>=P[P.length-1][0])a=b=P[P.length-1];else for(let i=0;i<P.length-1;i++){if(t>=P[i][0]&&t<P[i+1][0]){a=P[i];b=P[i+1];break;}}
 const q=a===b?0:eio(prog(t,a[0],b[0]));const z=lerp(a[1],b[1],q),hx=0.5/z,hy=0.5/z;return {z,cx:clamp(lerp(a[2],b[2],q),hx,1-hx),cy:clamp(lerp(a[3],b[3],q),hy,1-hy)};}
function replayAt(t){
 const R=F.kb.replay;
 if(t<R.dragEnd+0.35)return {kind:'connect2',ts:R.from};
 let st=R.steps[0];for(const s of R.steps)if(t>=s.t)st=s;
 if(R.play&&t>=R.play.s){const P=R.play;const ct=(t-P.s)*P.rate;const i=clamp(Math.floor((P.from+ct)*24),0,F.kb.clips[P.clip]-1);return {kind:'ok',img:`${A}frames/${P.clip}/f${String(i+1).padStart(3,'0')}.jpg`,ts:P.sec0+Math.floor(ct),ir:false,count:(P.from+ct)>=P.exitAt?'46 / 应到 46':'47 / 应到 46',playing:true,rate:P.rate};}
 return {kind:st.kind||'ok',img:st.img.startsWith('c')?`${A}frames/${st.img}.jpg`:`${TH}kb_${st.img}.jpg`,ts:st.sec,ir:false,count:st.count};
}
function replaySec(t){const R=F.kb.replay;if(t<R.dragStart)return R.from;const D=R.drag2;if(D&&t>=D.s&&t<D.e+0.05)return Math.round(lerp(D.from,D.to,eio(prog(t,D.s,D.e))));if(t<R.dragEnd)return Math.round(lerp(R.from,R.to,eio(prog(t,R.dragStart,R.dragEnd))));const v=replayAt(t);return v.ts;}
function ruler(sec){
 const pps=1.6;let ticks='';const s0=sec-130,s1=sec+130;
 for(let s=Math.ceil(s0/10)*10;s<=s1;s+=10){const x=196.5+(s-sec)*pps;const major=s%60===0;ticks+=`<div class="a" style="left:${x}px;top:${major?0:8}px;width:1px;height:${major?20:12}px;background:${major?'#9a9a9a':'#5a5a5a'}"></div>${major?`<div class="a" style="left:${x-18}px;top:24px;width:36px;text-align:center;font:400 10px InterV;color:#8a8a8a">${pad(Math.floor(s/3600))}:${pad(Math.floor(s/60)%60)}</div>`:''}`;}
 const rec0=19*3600,rec1=F.kb.replay.recEnd;const bx0=196.5+(rec0-sec)*pps,bx1=196.5+(rec1-sec)*pps;
 return `<div class="a" style="left:0;top:0;width:393px;height:44px;overflow:hidden"><div class="a" style="left:${Math.max(-10,bx0)}px;top:6px;width:${Math.max(0,Math.min(403,bx1)-Math.max(-10,bx0))}px;height:16px;background:rgba(46,120,230,.35)"></div>${ticks}</div><div class="a" style="left:195.5px;top:-6px;width:2px;height:34px;background:#ff9f0a;border-radius:1px"></div>`;}
function kbView(t,seg){
 const mode=(seg&&seg.mode)||'live';
 let v,count,zoom;
 if(mode==='replay'){v=replayAt(t);count=v.count;zoom=replayZoom(t);if(v.kind==='connect2')v={kind:'connect'};}
 else{v=liveAt(t);count=countAt(t);zoom=zoomAt(t);}
 CAMN=camAt(t);
 const cap=`<div class="a" style="right:8px;top:56px;width:87px;height:32px;border-radius:16px;border:.5px solid rgba(255,255,255,.22);background:rgba(0,0,0,.25);display:flex;align-items:center"><div style="flex:1;display:flex;justify-content:center;gap:3px"><div style="width:5px;height:5px;border-radius:3px;background:#fff"></div><div style="width:7px;height:7px;border-radius:4px;background:#fff;margin-top:-1px"></div><div style="width:5px;height:5px;border-radius:3px;background:#fff"></div></div><div style="width:.5px;height:18px;background:rgba(255,255,255,.25)"></div><div style="flex:1;display:flex;justify-content:center"><div style="width:16px;height:16px;border-radius:8px;border:2px solid #fff;display:flex;align-items:center;justify-content:center;${tapped('capsule',t,0.12,0.25)?'opacity:.5':''}"><div style="width:5px;height:5px;border-radius:3px;background:#fff"></div></div></div></div>`;
 const nav=`<div class="a" style="left:0;top:0;width:393px;height:${VT}px;background:#111"><div class="a" style="left:13px;top:65px">${G.back()}</div><div class="a cjk" style="left:0;width:393px;top:62px;text-align:center;font:500 17px 'Noto Sans CJK SC';color:#ededed">看班</div>${cap}</div>`;
 const live=mode==='live';const off=v.kind==='offline';
 const tool=`<div class="a" style="left:0;top:${VT+VH}px;width:393px;height:44px;background:#161616;display:flex;align-items:center;padding:0 14px;gap:7px"><div style="width:7px;height:7px;border-radius:4px;background:${live?(off?'#666':'#ff3b30'):'#8a8a8a'}"></div><div class="cjk" style="font:400 13px 'Noto Sans CJK SC';color:#d6d6d6">${live?(off?'离线':'实时'):'回放'} · 标清</div><div style="flex:1"></div><div style="display:flex;gap:20px;align-items:center">${kbIcons('#d6d6d6',soundOn(t),tapped('sound',t,0.12,0.25))}</div></div>`;
 const tabs=`<div class="a" style="left:${196.5-92}px;top:${VT+VH+58}px;width:184px;height:32px;border-radius:9px;background:#1f1f21;display:flex;padding:2px">${['实时','回放'].map((x,i)=>{const sel=(i===0)===live;const pr=i===1&&tapped('tabReplay',t,0.12,0.2);return `<div class="cjk" style="flex:1;border-radius:7px;${sel?'background:#3a3a3d':''};${pr?'background:#2c2c2e':''};text-align:center;font:${sel?500:400} 14px/28px 'Noto Sans CJK SC';color:${sel?'#fff':'#9a9a9a'}">${x}</div>`;}).join('')}</div>`;
 let lower='';
 if(live){const night=clockSec(t)>=21*3600+40*60;
  const row=(k,val,y,extra='')=>`<div class="a cjk" style="left:16px;top:${y}px;font:400 14px 'Noto Sans CJK SC';color:#8a8a8a">${k}</div><div class="a cjk" style="left:96px;top:${y}px;font:400 14px 'Noto Sans CJK SC';color:#d8d8d8;${extra}">${val}</div>`;
  lower=`<div class="a" style="left:12px;top:${VT+VH+104}px;width:369px;height:178px;border-radius:12px;background:#1c1c1e"><div class="a cjk" style="left:16px;top:14px;font:500 17px 'Noto Sans CJK SC';color:#efefef">高一(7)班 · ${night?'已下课':'晚自习'}</div><div class="a cjk" style="right:16px;top:17px;font:400 13px 'Noto Sans CJK SC';color:#8a8a8a">${night?'':'第二节'}</div><div class="a" style="left:16px;right:16px;top:50px;height:.5px;background:#2c2c2e"></div>${row('晚自习','19:00–21:40',64)}${row('班主任','王老师',94)}${camRow(t)}<div class="a" style="left:96px;top:153px;display:flex;align-items:center;gap:6px"><div style="width:7px;height:7px;border-radius:4px;background:${off?'#ff453a':'#30d158'}"></div><div class="cjk" style="font:400 13px 'Noto Sans CJK SC';color:${off?'#ff6961':'#8fd19e'}">${off?'设备离线':'设备在线'}</div></div><div class="a cjk" style="left:16px;top:152px;font:400 14px 'Noto Sans CJK SC';color:#8a8a8a">状态</div></div>
  <div class="a cjk" style="left:0;width:393px;top:${VT+VH+300}px;text-align:center;font:400 11.5px 'Noto Sans CJK SC';color:#5f5f5f">仅供本班家长查看，请勿截图、录屏外传</div>`;}
 else{const sec=replaySec(t);const R=F.kb.replay;const playing=v.playing;
  const btn=(x,ic,pr)=>`<div class="a" style="left:${x-24}px;top:${VT+VH+232}px;width:48px;height:48px;border-radius:24px;background:${pr?'#3a3a3d':'#232325'};display:flex;align-items:center;justify-content:center">${ic}</div>`;
  const prev=`<svg width="20" height="18" viewBox="0 0 20 18"><path d="M3 2v14" stroke="#e6e6e6" stroke-width="2" stroke-linecap="round"/><path d="M17 2 7 9l10 7z" fill="#e6e6e6"/></svg>`,next=`<svg width="20" height="18" viewBox="0 0 20 18"><path d="M17 2v14" stroke="#e6e6e6" stroke-width="2" stroke-linecap="round"/><path d="M3 2l10 7-10 7z" fill="#e6e6e6"/></svg>`;
  const pp=playing?`<svg width="16" height="18" viewBox="0 0 16 18"><rect x="2" y="2" width="4" height="14" rx="1" fill="#fff"/><rect x="10" y="2" width="4" height="14" rx="1" fill="#fff"/></svg>`:`<svg width="16" height="18" viewBox="0 0 16 18"><path d="M3 2l12 7-12 7z" fill="#fff"/></svg>`;
  lower=`<div class="a cjk" style="left:16px;top:${VT+VH+108}px;font:400 14px 'Noto Sans CJK SC';color:#d8d8d8">2026-11-09 <span style="color:#8a8a8a">▾</span></div>${playing?`<div class="a" style="right:16px;top:${VT+VH+106}px;padding:2px 9px;border-radius:10px;background:#2c2c2e;font:500 12px InterV;color:#fff">${v.rate}x</div>`:''}
  <div class="a" style="left:0;width:393px;top:${VT+VH+132}px;text-align:center;font:600 24px InterV;color:#fff;letter-spacing:.5px">${fmtSec(sec)}</div>
  <div class="a" style="left:0;top:${VT+VH+176}px;width:393px;height:44px">${ruler(sec)}</div>
  ${btn(110,prev,false)}${btn(196.5,pp,tapped('play',t,0.12,0.2))}${btn(283,next,tapped('next',t,0.12,0.2))}
  <div class="a cjk" style="left:0;width:393px;top:${VT+VH+294}px;text-align:center;font:400 11.5px 'Noto Sans CJK SC';color:#5f5f5f">录像保存 7 天 · 仅供本班家长查看</div>`;}
 return `<div class="L" style="background:#111">${videoBox(t,v,count,zoom)}${tool}${tabs}${lower}${nav}${homeBar()}</div>`;
}

// ---------- WeChat incoming video call (camera preview off) ----------
function callView(t){
 const ic={
  bell:`<svg width="15" height="16" viewBox="0 0 16 16"><path d="M8 2.2c-2.3 0-3.9 1.8-3.9 4v2.6L2.9 11h10.2l-1.2-2.2V6.2c0-2.2-1.6-4-3.9-4z" fill="#f2f2f2"/><path d="M6.4 12.4a1.7 1.7 0 0 0 3.2 0z" fill="#f2f2f2"/><path d="M2.6 2.4l10.8 11.2" stroke="#3a3b40" stroke-width="2.8"/><path d="M2.6 2.4l10.8 11.2" stroke="#f2f2f2" stroke-width="1.3" stroke-linecap="round"/></svg>`,
  flip:`<svg width="30" height="26" viewBox="0 0 28 24"><path d="M3 7h5l2-3h8l2 3h5v14H3z" fill="none" stroke="#fff" stroke-width="1.7" stroke-linejoin="round"/><path d="M9.5 13.5a4.5 4.5 0 0 1 8-2.6M18.5 14.5a4.5 4.5 0 0 1-8 2.6" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/><path d="M17.8 8.4v2.8H15M10.2 19.6v-2.8H13" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  blur:`<svg width="27" height="27" viewBox="0 0 26 26"><rect x="3" y="3" width="20" height="20" rx="3" fill="none" stroke="#fff" stroke-width="1.7"/><path d="M5 9l4-4M5 14l9-9M5 19l14-14M9 21l12-12M14 21l7-7" stroke="#fff" stroke-width="1" opacity=".55"/><circle cx="13" cy="11" r="3.3" fill="#fff"/><path d="M7 21c.8-3.6 3.2-5.4 6-5.4s5.2 1.8 6 5.4z" fill="#fff"/></svg>`,
  cam:`<svg width="30" height="24" viewBox="0 0 28 22"><rect x="2" y="5" width="17" height="13" rx="2.5" fill="#fff"/><path d="M19 9.5l6-3.5v11l-6-3.5z" fill="#fff"/><path d="M3.5 2l20.5 18.5" stroke="#4a4b52" stroke-width="3.6" stroke-linecap="round"/><path d="M3.5 2l20.5 18.5" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/></svg>`,
  down:`<svg width="36" height="36" viewBox="0 0 24 24"><path d="M3.2 13.9c-.5-.5-.6-1.3-.1-1.9 4.9-4.6 12.9-4.6 17.8 0 .5.6.4 1.4-.1 1.9l-1.6 1.5c-.5.4-1.2.5-1.7.1l-1.9-1.4c-.4-.3-.6-.7-.6-1.2v-1.6c-2-.7-4.1-.7-6.1 0v1.6c0 .5-.2.9-.6 1.2l-1.9 1.4c-.5.4-1.2.3-1.7-.1z" fill="#fff"/></svg>`,
  up:`<svg width="33" height="33" viewBox="0 0 24 24"><path d="M6.6 2.8c.6-.4 1.4-.3 1.8.3l2 2.9c.4.6.3 1.4-.2 1.9l-1.3 1.2c.9 2 2.4 3.6 4.3 4.6l1.3-1.2c.5-.5 1.3-.6 1.9-.2l2.9 2c.6.4.7 1.2.3 1.8l-1.2 1.8c-.6.9-1.7 1.4-2.8 1.2C9.9 18.1 5.9 14.1 4.9 8.4c-.2-1.1.3-2.2 1.2-2.8z" fill="#fff"/></svg>`};
 const opt=(x,inner,label,circ,dim)=>`<div class="a" style="left:${x-40}px;top:470px;width:80px;display:flex;flex-direction:column;align-items:center;opacity:${dim?.42:1}"><div style="width:58px;height:58px;border-radius:29px;${circ?'background:rgba(255,255,255,.2);':''}display:flex;align-items:center;justify-content:center">${inner}</div><div class="cjk" style="margin-top:7px;font:400 12.5px 'Noto Sans CJK SC';color:rgba(255,255,255,.88);white-space:nowrap">${label}</div></div>`;
 const big=(x,col,inner,label)=>`<div class="a" style="left:${x-45}px;top:568px;width:90px;display:flex;flex-direction:column;align-items:center"><div style="width:72px;height:72px;border-radius:36px;background:${col};display:flex;align-items:center;justify-content:center">${inner}</div><div class="cjk" style="margin-top:11px;font:400 14px 'Noto Sans CJK SC';color:rgba(255,255,255,.92)">${label}</div></div>`;
 return `<div class="L" style="background:#15161a;overflow:hidden">
  <div class="a" style="left:-60px;top:-60px;width:513px;height:972px;background:url(${TH}avatar_wang.jpg) center/cover;filter:blur(42px) brightness(.5) saturate(1.15)"></div>
  <div class="a" style="inset:0;background:linear-gradient(180deg,rgba(12,13,18,.38),rgba(12,13,18,.18) 45%,rgba(12,13,18,.42))"></div>
  <div class="a cjk" style="left:16px;top:58px;height:34px;padding:0 14px 0 12px;border-radius:17px;background:rgba(255,255,255,.14);display:flex;align-items:center;gap:6px;font:400 14.5px 'Noto Sans CJK SC';color:#f2f2f2">${ic.bell}忽略</div>
  <div class="a" style="left:${196.5-46}px;top:196px;width:92px;height:92px;border-radius:10px;overflow:hidden"><img src="${TH}avatar_wang.jpg" style="width:100%;height:100%;object-fit:cover;display:block"></div>
  <div class="a cjk" style="left:0;width:393px;top:302px;text-align:center;font:500 24px 'Noto Sans CJK SC';color:#fff">王老师</div>
  <div class="a cjk" style="left:0;width:393px;top:430px;text-align:center;font:400 15px 'Noto Sans CJK SC';color:rgba(255,255,255,.6)">邀请你视频通话</div>
  ${opt(112,ic.flip,'翻转',false,true)}${opt(196.5,ic.blur,'模糊背景',false,true)}${opt(281,ic.cam,'摄像头已关',true,false)}
  ${big(112,'#fa5151',ic.down,'拒绝')}${big(281,'#07c160',ic.up,'接听')}
 </div>`;
}

// ---------- v8 additions ----------
let CAMN=1;
function lastOf(list,t,def){let v=def;for(const x of (list||[]))if(t>=x[0])v=x[1];return v;}
function soundOn(t){return !!lastOf(F.sound,t,0);}
function camAt(t){return lastOf(F.cams,t,1);}
function camRow(t){const c=camAt(t);const pr=tapped('cam2',t,0.12,0.22);
 const pill=(n,label)=>{const sel=c===n;return `<div class="cjk" style="padding:0 10px;height:24px;border-radius:12px;font:${sel?500:400} 12.5px/24px 'Noto Sans CJK SC';${sel?'background:#3a3a3d;color:#fff':'border:.5px solid #3a3a3d;color:#9a9a9a'};${n===2&&pr?'background:#4a4a4e':''}">${label}</div>`;};
 return `<div class="a cjk" style="left:16px;top:124px;font:400 14px 'Noto Sans CJK SC';color:#8a8a8a">机位</div><div class="a" style="left:92px;top:121px;display:flex;gap:8px">${pill(1,'机位1 · 前门上方')}${pill(2,'机位2 · 后墙')}</div>`;}
// WeChat outgoing voice call (waiting for the callee)
function vcallView(t){
 const V=F.vcall;const who=V.who;const av=avOf(who);
 const dots='.'.repeat(1+Math.floor((t*1.6)%3));
 const ic={
  min:`<svg width="26" height="26" viewBox="0 0 26 26"><path d="M4 10h6V4M22 16h-6v6" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 10 3.5 3.5M16 16l6.5 6.5" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/></svg>`,
  mic:`<svg width="22" height="26" viewBox="0 0 26 30"><rect x="8.5" y="3" width="9" height="15" rx="4.5" fill="#1a1a1a"/><path d="M4.5 14a8.5 8.5 0 0 0 17 0M13 22.5V27" fill="none" stroke="#1a1a1a" stroke-width="2.2" stroke-linecap="round"/></svg>`,
  spk:`<svg width="26" height="24" viewBox="0 0 30 28"><path d="M3 10h5l7-6v20l-7-6H3z" fill="#1a1a1a"/><path d="M19.5 9.5a6 6 0 0 1 0 9M22.8 6.2a10.6 10.6 0 0 1 0 15.6" fill="none" stroke="#1a1a1a" stroke-width="2.1" stroke-linecap="round"/></svg>`,
  cam:`<svg width="26" height="18" viewBox="0 0 26 18"><rect x="1" y="1.5" width="16.5" height="15" rx="3.2" fill="#1a1a1a"/><path d="M18.5 7.2 25 3.4v11.2l-6.5-3.8z" fill="#1a1a1a"/></svg>`,
  blur:`<svg width="24" height="24" viewBox="0 0 24 24"><rect x="2.5" y="2.5" width="19" height="19" rx="3.5" fill="none" stroke="#fff" stroke-width="1.7"/><circle cx="12" cy="9.6" r="3.1" fill="#fff"/><path d="M6 19.2c1.1-3.1 3.3-4.7 6-4.7s4.9 1.6 6 4.7z" fill="#fff"/><path d="M3.5 9 9 3.5M3.5 15 15 3.5M15.5 20.5l5-5" stroke="#fff" stroke-width="1" opacity=".6"/></svg>`,
  flip:`<svg width="26" height="26" viewBox="0 0 26 26"><path d="M20.6 10.6A8 8 0 0 0 6.2 8.1M5.4 15.4A8 8 0 0 0 19.8 17.9" fill="none" stroke="#fff" stroke-width="1.9" stroke-linecap="round"/><path d="M6.4 3.8v4.6H11M19.6 22.2v-4.6H15" fill="none" stroke="#fff" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  down:`<svg width="32" height="32" viewBox="0 0 24 24"><path d="M3.2 13.9c-.5-.5-.6-1.3-.1-1.9 4.9-4.6 12.9-4.6 17.8 0 .5.6.4 1.4-.1 1.9l-1.6 1.5c-.5.4-1.2.5-1.7.1l-1.9-1.4c-.4-.3-.6-.7-.6-1.2v-1.6c-2-.7-4.1-.7-6.1 0v1.6c0 .5-.2.9-.6 1.2l-1.9 1.4c-.5.4-1.2.3-1.7-.1z" fill="#fff"/></svg>`};
 const y2=H-34-60, y1=y2-104;
 const btn=(x,y,d,bg,inner,label)=>`<div class="a" style="left:${x-45}px;top:${y}px;width:90px;display:flex;flex-direction:column;align-items:center"><div style="width:${d}px;height:${d}px;border-radius:${d/2}px;background:${bg};display:flex;align-items:center;justify-content:center">${inner}</div>${label?`<div class="cjk" style="margin-top:8px;font:400 12px 'Noto Sans CJK SC';color:rgba(255,255,255,.92);white-space:nowrap;text-shadow:0 0 3px rgba(0,0,0,.6)">${label}</div>`:''}</div>`;
 return `<div class="L" style="background:#0d0d0f;overflow:hidden">
  <img class="a" src="${TH}selfcam.jpg" style="left:0;top:0;width:393px;height:${H}px;object-fit:cover;display:block">
  ${IRN(t,0.06)}
  <div class="a" style="inset:0;background:linear-gradient(180deg,rgba(0,0,0,.42),rgba(0,0,0,.08) 34%,rgba(0,0,0,0) 58%,rgba(0,0,0,.45))"></div>
  <div class="a" style="left:18px;top:60px;${tapped('vmin',t,0.12,0.2)?'opacity:.45':''}">${ic.min}</div>
  <div class="a" style="left:${196.5-41}px;top:118px;width:82px;height:82px;border-radius:9px;overflow:hidden"><img src="${av}" style="width:100%;height:100%;object-fit:cover;display:block"></div>
  <div class="a cjk" style="left:0;width:393px;top:214px;text-align:center;font:500 22px 'Noto Sans CJK SC';color:#fff;text-shadow:0 0 4px rgba(0,0,0,.5)">${nameOf(who)}</div>
  <div class="a cjk" style="left:0;width:393px;top:252px;text-align:center;font:400 14px 'Noto Sans CJK SC';color:rgba(255,255,255,.78);text-shadow:0 0 4px rgba(0,0,0,.5)">正在等待对方接受邀请<span style="display:inline-block;width:18px;text-align:left">${dots}</span></div>
  ${btn(80,y1,60,'#f2f2f2',ic.mic,'麦克风已开')}${btn(196.5,y1,60,'#f2f2f2',ic.spk,'扬声器已开')}${btn(313,y1,60,'#f2f2f2',ic.cam,'摄像头已开')}
  ${btn(80,y2+6,52,'rgba(40,40,42,.72)',ic.blur,'')}${btn(196.5,y2,64,'#fa5151',ic.down,'')}${btn(313,y2+6,52,'rgba(40,40,42,.72)',ic.flip,'')}
 </div>`;
}
const FL={x:317,y:122,w:66,h:80};
function floatHtml(t,seg){
 const f=F.float;if(!f||t<f.s||t>=f.e+0.3||!seg||seg.type==='black'||seg.type==='vcall'||seg.type==='vcallIn')return '';
 if(seg.type==='vcallMin'&&t<seg.e-0.12)return '';
 const op=Math.min(prog(t,f.s,f.s+0.15),1-prog(t,f.e,f.e+0.3));
 if(f.connect&&t>=f.connect){const q=eo(prog(t,f.connect,f.connect+0.3));const w=lerp(FL.w,74,q),h=lerp(FL.h,128,q),x=393-10-w;const fy=f.drag?lerp(FL.y,f.dragY,eo(prog(t,f.drag,f.drag+0.45))):FL.y;
  const sec=Math.max(0,Math.floor(t-f.connect));const tm=String(Math.floor(sec/60)).padStart(2,'0')+':'+String(sec%60).padStart(2,'0');
  return `<div class="a" style="left:${x}px;top:${fy}px;width:${w}px;height:${h}px;border-radius:10px;background:#040404;box-shadow:0 4px 16px rgba(0,0,0,.55);border:.5px solid rgba(255,255,255,.08);z-index:25;overflow:hidden;opacity:${op}"><div class="a" style="left:0;right:0;bottom:7px;text-align:center;font:500 11px InterV;color:rgba(255,255,255,.9);opacity:${q}">${tm}</div></div>`;}
 const failed=f.fail&&t>=f.fail;const col=failed?'#9a9a9a':'#07c160';
 const cam=`<svg width="26" height="18" viewBox="0 0 26 18"><rect x="1" y="1.5" width="16.5" height="15" rx="3.2" fill="${col}"/><path d="M18.5 7.2 25 3.4v11.2l-6.5-3.8z" fill="${col}"/></svg>`;
 return `<div class="a" style="left:${FL.x}px;top:${FL.y}px;width:${FL.w}px;height:${FL.h}px;border-radius:10px;background:#2c2c2e;box-shadow:0 4px 16px rgba(0,0,0,.5);z-index:25;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;opacity:${op}">${f.video?cam:G.handset(col,0,26)}<div class="cjk" style="font:400 11px 'Noto Sans CJK SC';color:${col};white-space:nowrap">${failed?'对方无应答':'等待接听'}</div></div>`;
}

function greenDot(t){const g=F.greenDot;if(!g||t<g)return '';return `<div class="a" style="left:266px;top:25.5px;width:7px;height:7px;border-radius:4px;background:#30d158;z-index:80;opacity:${prog(t,g,g+0.15)}"></div>`;}
// ---------- composition ----------
function viewFor(spec,t){switch(spec.type){case 'chat':return chatView(spec.chat,t);case 'list':return listView(t,spec);case 'svc':return svcView(t);case 'kb':return kbView(t,spec);case 'call':return callView(t);case 'vcall':return vcallView(t);}return '';}
function endCard(t){return `<div class="L" style="background:#000;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:${prog(t,F.cardAt,F.cardAt+0.6)}"><div class="cjk" style="font:400 30px 'Noto Sans CJK SC';letter-spacing:8px;color:#d8d8d8;margin-left:8px">已就寝</div><div class="cjk" style="margin-top:22px;font:400 13px 'Noto Sans CJK SC';color:#6f6f6f">虚构演绎 · 人物与聊天记录均为虚构</div></div>`;}
function postFix2(){
 for(const el of root.querySelectorAll('[data-scroll]')){const v=el.getAttribute('data-scroll');if(!v)continue;const sc=JSON.parse(v);const row=el.querySelector(`[data-mid="${sc.mid}"]`);const box=el.parentElement;if(!row||!box)continue;
  const br=box.getBoundingClientRect(),rr=row.getBoundingClientRect();const target=br.height*0.42-((rr.top-br.top)+rr.height/2);el.style.transform=`translateY(${Math.max(0,target)*sc.p}px)`;}
}
function sheetHtml(t){
 const s=F.sheet;if(!s||t<s.s||t>=s.e+0.25)return '';
 const p=Math.min(eo(prog(t,s.s,s.s+0.26)),1-eo(prog(t,s.e,s.e+0.25)));const pr=t>=s.tapAt-0.12&&t<s.e;const pv=pr&&s.pick==='video',pa=pr&&s.pick!=='video';
 return `<div class="L" style="background:rgba(0,0,0,${0.45*p});z-index:30"></div><div class="a cjk" style="left:0;top:${H-(186+SAFE)*p}px;width:393px;height:${186+SAFE}px;background:#2c2c2c;border-radius:12px 12px 0 0;z-index:31;font:400 17px 'Noto Sans CJK SC';color:#e8e8e8;text-align:center">
 <div style="height:56px;line-height:56px;${pv?'background:#383838':''}">视频通话</div><div style="height:.5px;background:#3d3d3d"></div><div style="height:56px;line-height:56px;${pa?'background:#383838':''}">语音通话</div><div style="height:8px;background:#1e1e1e"></div><div style="height:56px;line-height:56px">取消</div></div>`;
}

function fmtDur(x){x=Math.max(0,Math.floor(x));const h=Math.floor(x/3600),m=Math.floor(x/60)%60,q=x%60;const p=n=>String(n).padStart(2,'0');return h?`${h}:${p(m)}:${p(q)}`:`${p(m)}:${p(q)}`;}
function detHtml(t,zz){
 const D=F.kb.det||[];let h='';const fs=clamp(4.4*Math.pow(zz,0.8),4.4,10.5),bw=clamp(0.6*Math.sqrt(zz),0.6,1.2);
 for(const d of D){if(t<d.s||t>=d.e)continue;const fade=Math.min(prog(t,d.s,d.s+0.18),1-prog(t,d.e-0.25,d.e));
  let bx=d.boxes;
  if(d.trk){const T=F.kb.tracks[d.trk];const fi=clamp(Math.floor((t-d.t0)*(d.rate||1)*24),0,T.n-1);
   bx=T.tracks.map(tr=>{const v=tr[fi];return [v[0],v[1],v[2]*1.08,v[3]*1.12,d.lab.replace('{sc}',v[4].toFixed(2))];});}
  else if(d.jit){const q=t*7.3,k=Math.floor(q),f=q-k,hh=n=>{const x=Math.sin(n*127.1+311.7)*43758.5453;return x-Math.floor(x)-0.5;},
   sm=(n,o)=>lerp(hh(n+o),hh(n+1+o),f*f*(3-2*f));
   bx=bx.map((b,i)=>[b[0]+d.jit*b[2]*sm(k,i*17),b[1]+d.jit*b[3]*sm(k,i*17+5),b[2]*(1+0.6*d.jit*sm(k,i*17+9)),b[3]*(1+0.6*d.jit*sm(k,i*17+9)),b[4]]);}
  bx.forEach((b,i)=>{const a0=d.s+(d.stagger||0)*i;if(t<a0)return;const op=fade*clamp((t-a0)/0.1,0,1);
   let lab=b[4];if(d.since!=null)lab=lab.replace('{dur}',fmtDur(clockSec(t)-d.since));
   h+=`<div class="a" style="left:${((b[0]-b[2]/2)*100).toFixed(3)}%;top:${((b[1]-b[3]/2)*100).toFixed(3)}%;width:${(b[2]*100).toFixed(3)}%;height:${(b[3]*100).toFixed(3)}%;border:${bw.toFixed(2)}px solid ${d.col};box-sizing:border-box;opacity:${op.toFixed(3)}"><div class="cjk" style="position:absolute;left:${-bw}px;bottom:100%;padding:0 ${(fs*0.32).toFixed(2)}px;background:${d.col};font:600 ${fs.toFixed(2)}px/${(fs*1.32).toFixed(2)}px 'Noto Sans CJK SC',InterV;color:#0b0b0b;white-space:nowrap">${lab}</div></div>`;});}
 return h;}
window.setTime=function(t){
 if(t>=F.blackAt){root.innerHTML=t<F.cardAt?'':endCard(t);return;}
 const seg=F.segments.find(s=>t>=s.s&&t<s.e)||F.segments[F.segments.length-1];const lp=prog(t,seg.s,seg.e);let body='',sm='normal';
 switch(seg.type){
  case 'lock':body=lockView(t,seg);sm='lock';break;
  case 'black':body='';sm='none';break;
  case 'sleep':body=wrap(viewFor(seg.from,seg.s-0.001),`opacity:${1-lp}`);sm=lp>.3?'none':'normal';break;
  case 'notifOpen':{const p=eio(lp);const ls=lockSegBefore(seg);const r={x:10,y:cardTop(0,ls.notifs.length),w:373,h:68};const x=lerp(r.x,0,p),y=lerp(r.y,0,p),w=lerp(r.w,W,p),h=lerp(r.h,H,p);
   body=wrap(lockView(seg.s-0.001,ls),`transform:scale(${lerp(1,1.06,p)});opacity:${1-p*.8}`)+`<div class="a" style="left:${x}px;top:${y}px;width:${w}px;height:${h}px;border-radius:${lerp(22,0,p)}px;overflow:hidden;background:#000"><div style="transform:scale(${w/W},${h/H});transform-origin:0 0;width:393px;height:${H}px;position:relative;opacity:${prog(lp,.15,.6)}">${viewFor(seg.to,t)}</div></div>`;sm=p<.5?'lock':'normal';break;}
  case 'chat':body=chatView(seg.chat,t);break;
  case 'list':body=listView(t,seg);break;
  case 'svc':body=svcView(t);break;
  case 'kb':body=kbView(t,seg);break;
  case 'mpOpen':{const p=eio(lp);body=viewFor(seg.from,seg.s-0.001)+`<div class="L" style="background:rgba(0,0,0,${0.35*p})"></div>`+wrap(kbView(t,seg.to),`transform:translateY(${(1-p)*H}px)`);break;}
  case 'mpClose':{const p=eio(lp);body=viewFor(seg.to,t)+`<div class="L" style="background:rgba(0,0,0,${0.35*(1-p)})"></div>`+wrap(kbView(seg.s-0.001,seg.from),`transform:translateY(${p*H}px)`);break;}
  case 'pop':case 'push':{const p=eio(lp);const back=seg.type==='pop';const under=back?viewFor(seg.to,t):viewFor(seg.from,seg.s-0.001),over=back?viewFor(seg.from,seg.s-0.001):viewFor(seg.to,t);const q=back?1-p:p;
   body=wrap(under,`transform:translateX(${-W*0.3*q}px)`)+`<div class="L" style="background:rgba(0,0,0,${0.25*q})"></div>`+wrap(over,`transform:translateX(${W*(1-q)}px);box-shadow:-6px 0 18px rgba(0,0,0,.35)`);break;}
  case 'tabSwitch':{const p=eio(lp);body=kbView(t,{mode:'replay'});break;}
  case 'callIn':{const p=eio(lp);body=kbView(seg.s-0.001,{mode:'replay'})+wrap(callView(t),`transform:translateY(${(1-p)*H}px)`);break;}
  case 'call':body=callView(t);break;
  case 'vcallIn':{const p=eio(lp);body=chatView(seg.chat,seg.s-0.001)+wrap(vcallView(t),`opacity:${p};transform:scale(${lerp(1.06,1,p)})`);break;}
  case 'vcall':body=vcallView(t);break;
  case 'vcallMin':{const p=eio(lp);const sx=lerp(1,FL.w/W,p),sy=lerp(1,FL.h/H,p);body=chatView(seg.chat,t)+`<div class="a" style="left:${lerp(0,FL.x,p)}px;top:${lerp(0,FL.y,p)}px;width:${W}px;height:${H}px;transform:scale(${sx},${sy});transform-origin:0 0;border-radius:${lerp(0,60,p)}px;overflow:hidden;opacity:${1-prog(lp,.55,1)}">${vcallView(seg.s-0.001)}</div>`;break;}
 }
 root.innerHTML=body+floatHtml(t,seg)+`<div class="L" style="pointer-events:none;z-index:60;opacity:${sm==='none'?0:1}">${statusBar(t,sm==='lock'?'lock':'normal')}</div>`+(sm==='none'&&seg.type==='black'?'':island(t))+(seg.type==='black'?'':bannerHtml(t)+greenDot(t));
 postFix2();
};
window.setTime(0);
})();
</script></body></html>
