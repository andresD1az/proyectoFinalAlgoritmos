import pathlib, textwrap

ROOT = pathlib.Path(__file__).parent.parent
OUT  = ROOT / "frontend" / "index.html"

# ── leer la parte ya escrita (CSS + HTML) ──────────────────────────
existing = OUT.read_text(encoding="utf-8")

JS = textwrap.dedent("""
<script>
const API='';
const YF='https://finance.yahoo.com/quote/';
const NM={EC:'Ecopetrol',CIB:'Bancolombia',GXG:'iShares Colombia',
  ILF:'Latin America 40',EWZ:'iShares Brazil',EWW:'iShares Mexico',
  SPY:'S&P 500 ETF',QQQ:'Nasdaq 100',DIA:'Dow Jones ETF',
  EEM:'Emerging Markets',VT:'Vanguard World',IEMG:'Core EM',
  GLD:'Gold SPDR',SLV:'Silver Trust',USO:'US Oil Fund',
  TLT:'Treasury 20Y',XLE:'Energy',XLF:'Financials',
  XLK:'Technology',VNQ:'Real Estate'};
let hmLoaded=false,rkLoaded=false,allLoaded=false,cache={};
let allTickers=Object.keys(NM);

function toggleSidebar(){
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('ov-lay').classList.toggle('show');
}
function closeSidebar(){
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('ov-lay').classList.remove('show');
}
const titles={ov:'Overview',cmp:'Comparar Activos',hm:'Mapa de Calor',
  cs:'Velas OHLC',rk:'Clasificacion de Riesgo',add:'Agregar Activo',
  all:'Todos los Activos',rp:'Reporte',auth:'Login',fx:'Tasa USD/COP',
  learn:'Academia',sim:'Simulador',admin:'Panel Admin',info:'Info Legal'};

function nav(el,id){
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.querySelectorAll('.sec').forEach(s=>s.classList.remove('on'));
  el.classList.add('active');
  document.getElementById('sec-'+id).classList.add('on');
  document.getElementById('ptitle').textContent=titles[id]||id;
  closeSidebar();
  if(id==='hm'&&!hmLoaded)loadHeatmap();
  if(id==='rk'&&!rkLoaded)loadRiesgo();
  if(id==='all'&&!allLoaded)loadAll();
  if(id==='cs')initCS();
  if(id==='fx')loadTasa();
  if(id==='learn')loadLecciones();
  if(id==='sim')loadSim();
  if(id==='admin')loadAdmin();
}
function populateSel(tickers){
  ['ca1','ca2','cst'].forEach(id=>{
    const s=document.getElementById(id);if(!s)return;
    s.innerHTML=tickers.map((t,i)=>
      `<option value="${t}"${i===(id==='ca2'?1:0)?' selected':''}>${t}${NM[t]?' - '+NM[t]:''}</option>`
    ).join('');
  });
}
async function f(path){
  if(cache[path])return cache[path];
  const r=await fetch(API+path);const d=await r.json();cache[path]=d;return d;
}
async function fno(path){const r=await fetch(API+path);return r.json();}

async function init(){
  try{
    const d=await fno('/activos');
    const tks=(d.activos||[]).map(a=>a.ticker||a);
    if(tks.length){
      allTickers=tks;
      Object.assign(NM,Object.fromEntries(d.activos.map(a=>[a.ticker,a.nombre||a.ticker])));
    }
  }catch{}
  populateSel(allTickers);checkStatus();loadOV();
}
async function checkStatus(){
  try{
    const d=await f('/health');
    if(d.estado==='ok'){
      document.getElementById('adot').classList.add('on');
      document.getElementById('atxt').textContent='API Online';
    }
  }catch{document.getElementById('atxt').textContent='Sin conexion';}
}
</script>
""")

JS2 = textwrap.dedent("""
<script>
async function loadOV(){
  try{
    const da=await fno('/activos');
    document.getElementById('st-act').textContent=(da.total||da.activos?.length||'');
    const d=await f('/reporte');
    const tot=d.seccion_1_datos?.filas_totales;
    if(tot)document.getElementById('st-reg').textContent=tot.toLocaleString();
    const top=(d.seccion_2_similitud?.pearson?.top_5||[]);
    document.getElementById('top-p').innerHTML=top.map((p,i)=>`
      <tr><td style="color:var(--txt3)">${i+1}</td>
      <td><a href="${YF+p.ticker1}" target="_blank" class="yfl">${p.ticker1}</a>
          &mdash; <a href="${YF+p.ticker2}" target="_blank" class="yfl">${p.ticker2}</a></td>
      <td class="mono">${p.valor.toFixed(4)}</td>
      <td><span class="badge ${p.valor>.9?'bg':'by'}">${p.valor>.9?'Muy alta':'Alta'}</span></td></tr>`
    ).join('')||'<tr><td colspan="4" style="padding:14px;color:var(--txt3)">Ejecutar pipeline de similitud primero</td></tr>';
    const rk=d.seccion_3_volatilidad?.ranking||[];
    if(rk.length){
      const c=rk.filter(x=>x.volatilidad_anual<.15).length;
      const m=rk.filter(x=>x.volatilidad_anual>=.15&&x.volatilidad_anual<.3).length;
      const a=rk.filter(x=>x.volatilidad_anual>=.3).length;
      document.getElementById('risk-sum').innerHTML=`<div style="display:flex;flex-direction:column;gap:10px;padding:4px 0">
        ${rbar('Conservadores',c,rk.length,'var(--green)')}
        ${rbar('Moderados',m,rk.length,'var(--yel)')}
        ${rbar('Agresivos',a,rk.length,'var(--red)')}</div>`;
    }
  }catch(e){console.error(e)}
  try{
    const items=await Promise.all(allTickers.slice(0,6).map(async t=>{
      try{
        const d=await f(`/precios?ticker=${t}&columna=cierre`);
        const p=d.datos||[];if(p.length<2)return null;
        const last=+p[p.length-1].cierre,prev=+p[p.length-2].cierre,chg=(last-prev)/prev*100;
        return `<div class="tick"><b>${t}</b><span class="pr">${last.toFixed(2)}</span><span class="${chg>=0?'up':'dn'}">${chg>=0?'+':''}${chg.toFixed(2)}%</span></div>`;
      }catch{return null;}
    }));
    document.getElementById('strip').innerHTML=items.filter(Boolean).join('');
  }catch{}
}
function rbar(lbl,n,tot,cl){
  const p=tot>0?n/tot*100:0;
  return `<div style="display:flex;align-items:center;gap:10px">
    <div style="width:90px;font-size:12px;color:var(--txt3)">${lbl}</div>
    <div class="vbar" style="flex:1;max-width:160px"><div class="vfill" style="width:${p}%;background:${cl}"></div></div>
    <b style="font-family:var(--mono);color:${cl};min-width:16px">${n}</b></div>`;
}

let pc={};
async function getPr(t){
  if(pc[t])return pc[t];
  const d=await f(`/precios?ticker=${t}&columna=cierre`);
  const v=(d.datos||[]).map(x=>+x.cierre);pc[t]=v;return v;
}
async function getSim(t1,t2,algo){
  try{
    const d=await f(`/similitud?algoritmo=${algo}`);
    const rs=d.resultados||[];
    const row=rs.find(r=>(r.ticker1===t1&&r.ticker2===t2)||(r.ticker1===t2&&r.ticker2===t1));
    return row?+row.valor:null;
  }catch{return null;}
}
async function comparar(){
  const t1=document.getElementById('ca1').value,t2=document.getElementById('ca2').value;
  document.getElementById('ctitle').textContent=`${t1} vs ${t2} % Cambio acumulado`;
  document.getElementById('line-wrap').innerHTML='<div class="ld"><div class="spin"></div>Calculando...</div>';
  ['v-eu','v-pe','v-co','v-dt'].forEach(id=>document.getElementById(id).textContent='-');
  try{const [p1,p2]=await Promise.all([getPr(t1),getPr(t2)]);drawLine(p1,p2,t1,t2);}
  catch(e){document.getElementById('line-wrap').innerHTML=`<p style="color:var(--red);padding:14px">${e.message}</p>`;}
  for(const[algo,id]of[['euclidiana','v-eu'],['pearson','v-pe'],['coseno','v-co'],['dtw','v-dt']]){
    const val=await getSim(t1,t2,algo);
    document.getElementById(id).textContent=val!=null?val.toFixed(4):'N/D';
  }
}
function drawLine(p1,p2,l1,l2){
  const n=Math.min(p1.length,p2.length);
  const s1=p1.slice(-n),s2=p2.slice(-n);
  const n1=s1.map(v=>((v-s1[0])/s1[0])*100),n2=s2.map(v=>((v-s2[0])/s2[0])*100);
  const W=900,H=250,PL=52,PR=12,PT=12,PB=32;
  const xs=W-PL-PR,ys=H-PT-PB;
  const all=[...n1,...n2],mn=Math.min(...all),mx=Math.max(...all),rng=mx-mn||1;
  const px=i=>PL+i/(n-1)*xs,py=v=>PT+(1-(v-mn)/rng)*ys;
  const pt=a=>a.map((v,i)=>`${i===0?'M':'L'}${px(i).toFixed(1)},${py(v).toFixed(1)}`).join(' ');
  const yL=[];for(let i=0;i<=4;i++){const v=mn+i/4*rng;yL.push({y:py(v),l:(v>=0?'+':'')+v.toFixed(1)+'%'});}
  const svg=`<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:100%;overflow:visible">
    <defs>
      <linearGradient id="g1" x2="0" y2="1"><stop offset="0%" stop-color="#10b981" stop-opacity=".2"/><stop offset="100%" stop-color="#10b981" stop-opacity="0"/></linearGradient>
      <linearGradient id="g2" x2="0" y2="1"><stop offset="0%" stop-color="#38bdf8" stop-opacity=".2"/><stop offset="100%" stop-color="#38bdf8" stop-opacity="0"/></linearGradient>
    </defs>
    ${yL.map(({y,l})=>`<line x1="${PL}" y1="${y.toFixed(1)}" x2="${W-PR}" y2="${y.toFixed(1)}" stroke="#1a2d4a" stroke-width="1"/>
    <text x="${PL-5}" y="${(y+4).toFixed(1)}" text-anchor="end" font-size="9" fill="#64748b">${l}</text>`).join('')}
    <path d="${pt(n1)} L${px(n-1)},${py(mn)} L${px(0)},${py(mn)} Z" fill="url(#g1)"/>
    <path d="${pt(n2)} L${px(n-1)},${py(mn)} L${px(0)},${py(mn)} Z" fill="url(#g2)"/>
    <path d="${pt(n1)}" fill="none" stroke="#10b981" stroke-width="2.5"/>
    <path d="${pt(n2)}" fill="none" stroke="#38bdf8" stroke-width="2.5"/>
    <g transform="translate(${PL},${H-6})">
      <circle cx="0" cy="0" r="5" fill="#10b981"/>
      <text x="10" y="4" font-size="12" fill="#10b981" font-weight="600">${l1}</text>
      <circle cx="60" cy="0" r="5" fill="#38bdf8"/>
      <text x="70" y="4" font-size="12" fill="#38bdf8" font-weight="600">${l2}</text>
    </g></svg>`;
  document.getElementById('line-wrap').innerHTML=`<div style="height:260px">${svg}</div>`;
}
</script>
""")

JS3 = textwrap.dedent("""
<script>
async function loadHeatmap(){
  hmLoaded=true;
  try{
    const d=await fno('/correlacion/matriz');
    const tks=d.tickers||[],mat=d.matriz||[];
    if(!tks.length){document.getElementById('hm-wrap').innerHTML='<p style="color:var(--txt3);padding:14px">Sin datos. Ejecutar pipeline de similitud primero.</p>';return;}
    drawHeatmap(tks,mat);
  }catch(e){document.getElementById('hm-wrap').innerHTML=`<p style="color:var(--red);padding:14px">${e.message}</p>`;}
}
function corColor(v){
  if(v>=0)return `rgb(${Math.round(16+(240-16)*(1-v))},185,${Math.round(129*v)})`;
  const t=-v;return `rgb(244,${Math.round(63+90*(1-t))},${Math.round(94*(1-t))})`;
}
function drawHeatmap(tks,mat){
  const n=tks.length,cell=32,lbl=48;
  const W=lbl+n*cell,H=lbl+n*cell;
  let rects='',xl='',yl='';
  for(let i=0;i<n;i++){
    xl+=`<text x="${lbl+i*cell+cell/2}" y="${lbl-4}" text-anchor="middle" font-size="8" fill="#64748b" transform="rotate(-45,${lbl+i*cell+cell/2},${lbl-4})">${tks[i]}</text>`;
    yl+=`<text x="${lbl-5}" y="${lbl+i*cell+cell/2+4}" text-anchor="end" font-size="9" fill="#64748b">${tks[i]}</text>`;
    for(let j=0;j<n;j++){
      const v=mat[i]?.[j]??0;
      rects+=`<rect x="${lbl+j*cell}" y="${lbl+i*cell}" width="${cell-1}" height="${cell-1}" fill="${corColor(v)}" rx="3"
        onmouseenter="showTip(event,'${tks[i]} vs ${tks[j]}: r=${v.toFixed(4)}')" onmouseleave="hideTip()"/>`;
    }
  }
  document.getElementById('hm-wrap').innerHTML=`<div style="overflow-x:auto"><svg width="${W}" height="${H}" style="display:block">${xl}${yl}${rects}</svg></div>`;
}
function showTip(e,t){const tp=document.getElementById('tip');tp.textContent=t;tp.style.display='block';tp.style.left=(e.clientX+12)+'px';tp.style.top=(e.clientY+12)+'px';}
function hideTip(){document.getElementById('tip').style.display='none';}

function initCS(){if(!document.getElementById('cst').options.length)populateSel(allTickers);}
function sma(arr,w){return arr.map((_,i)=>i<w-1?null:arr.slice(i-w+1,i+1).reduce((a,b)=>a+b,0)/w);}
async function loadCS(){
  const tk=document.getElementById('cst').value,n=+document.getElementById('csp').value;
  const w1=+document.getElementById('sm1').value,w2=+document.getElementById('sm2').value;
  document.getElementById('cs-title').textContent=`${tk} - Ultimos ${n} dias`;
  document.getElementById('cs-wrap').style.display='block';
  document.getElementById('cs-wrap').innerHTML='<div class="ld"><div class="spin"></div>Cargando...</div>';
  document.getElementById('cv').style.display='none';
  try{
    const d=await fno(`/precios/ohlcv?ticker=${tk}&n=${n+Math.max(w1,w2)}`);
    const datos=(d.datos||[]).slice(-n);
    if(!datos.length){document.getElementById('cs-wrap').innerHTML='<p style="color:var(--red);padding:14px">Sin datos OHLCV</p>';return;}
    drawCS(datos,sma(datos.map(x=>x.cierre),w1),sma(datos.map(x=>x.cierre),w2));
  }catch(e){document.getElementById('cs-wrap').innerHTML=`<p style="color:var(--red);padding:14px">${e.message}</p>`;}
}
function drawCS(datos,smaf,smas){
  const cv=document.getElementById('cv');
  const W=cv.parentElement.offsetWidth||900,H=380;
  cv.width=W;cv.height=H;const ctx=cv.getContext('2d');
  ctx.fillStyle='#0c1526';ctx.fillRect(0,0,W,H);
  const n=datos.length,PL=60,PR=14,PT=18,PB=56;
  const xs=W-PL-PR,ys=H-PT-PB,pw=xs/n,cw=Math.max(pw*.65,2);
  const mn=Math.min(...datos.map(d=>d.minimo)),mx=Math.max(...datos.map(d=>d.maximo)),rng=mx-mn||1;
  const px=i=>PL+i*pw+pw/2,py=v=>PT+(1-(v-mn)/rng)*ys;
  ctx.strokeStyle='#1a2d4a';ctx.lineWidth=1;
  for(let i=0;i<=5;i++){
    const v=mn+i/5*rng,y=py(v);
    ctx.beginPath();ctx.moveTo(PL,y);ctx.lineTo(W-PR,y);ctx.stroke();
    ctx.fillStyle='#64748b';ctx.font='10px JetBrains Mono,monospace';ctx.textAlign='right';
    ctx.fillText('$'+v.toFixed(2),PL-5,y+4);
  }
  for(let i=0;i<n;i++){
    const{apertura:o,maximo:h,minimo:l,cierre:c}=datos[i];
    const bull=c>=o,col=bull?'#10b981':'#f43f5e',cx=px(i);
    ctx.strokeStyle=col;ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(cx,py(h));ctx.lineTo(cx,py(l));ctx.stroke();
    const top=py(Math.max(o,c)),bot=py(Math.min(o,c)),bh=Math.max(bot-top,1);
    ctx.fillStyle=col;ctx.fillRect(cx-cw/2,top,cw,bh);
  }
  const drawSMA=(arr,color)=>{
    ctx.strokeStyle=color;ctx.lineWidth=1.8;ctx.beginPath();
    let first=true;arr.forEach((v,i)=>{if(v===null)return;if(first){ctx.moveTo(px(i),py(v));first=false;}else ctx.lineTo(px(i),py(v));});
    ctx.stroke();
  };
  drawSMA(smaf,'#38bdf8');drawSMA(smas,'#f59e0b');
  ctx.fillStyle='#64748b';ctx.textAlign='center';ctx.font='9px JetBrains Mono,monospace';
  const step=Math.max(1,Math.floor(n/10));
  for(let i=0;i<n;i+=step)ctx.fillText(datos[i].fecha.slice(5),px(i),H-PT-8);
  document.getElementById('cs-wrap').style.display='none';cv.style.display='block';
}

async function loadRiesgo(){
  rkLoaded=true;
  try{
    const d=await fno('/riesgo/clasificacion');
    const activos=d.activos||[],conteo=d.conteo||{};
    document.getElementById('cnt-c').textContent=conteo['Conservador']||0;
    document.getElementById('cnt-m').textContent=conteo['Moderado']||0;
    document.getElementById('cnt-a').textContent=conteo['Agresivo']||0;
    const maxV=Math.max(...activos.map(a=>a.vol_pct));
    const rows=activos.map((a,i)=>{
      const bcls=a.categoria==='Conservador'?'bg':a.categoria==='Moderado'?'by':'br';
      const bc=a.categoria==='Conservador'?'var(--green)':a.categoria==='Moderado'?'var(--yel)':'var(--red)';
      const sc=a.sharpe>1?'var(--green)':a.sharpe>0?'var(--yel)':'var(--red)';
      return `<tr>
        <td style="color:var(--txt3)">${i+1}</td>
        <td><b style="color:var(--acc)">${a.ticker}</b></td>
        <td style="color:var(--txt3)">${NM[a.ticker]||''}</td>
        <td class="mono">${a.vol_pct}%</td>
        <td style="width:120px"><div class="vbar"><div class="vfill" style="width:${Math.round(a.vol_pct/maxV*100)}%;background:${bc}"></div></div></td>
        <td><span class="badge ${bcls}">${a.categoria}</span></td>
        <td class="mono" style="color:${sc}">${a.sharpe}</td>
        <td class="mono">${a.var95_pct}%</td></tr>`;
    }).join('');
    document.getElementById('rk-wrap').innerHTML=`<div class="table-wrap"><table>
      <thead><tr><th>#</th><th>Ticker</th><th>Nombre</th><th>Vol. Anual</th><th>Barra</th><th>Categoria</th><th>Sharpe</th><th>VaR 95%</th></tr></thead>
      <tbody>${rows}</tbody></table></div>`;
  }catch(e){document.getElementById('rk-wrap').innerHTML=`<p style="color:var(--red);padding:14px">${e.message}</p>`;}
}
</script>
""")

JS4 = textwrap.dedent("""
<script>
async function agregarActivo(){
  const btn=document.getElementById('add-btn');
  const tk=document.getElementById('add-tk').value.trim().toUpperCase();
  const nm=document.getElementById('add-nm').value.trim()||tk;
  const mkt=document.getElementById('add-mkt').value;
  const res=document.getElementById('add-res');
  if(!tk){res.className='add-result err';res.style.display='block';res.textContent='Escribe un ticker primero.';return;}
  btn.disabled=true;btn.textContent='Descargando...';
  res.className='add-result';res.style.display='block';res.textContent=`Descargando 5 anos de datos para ${tk}...`;
  try{
    const r=await fetch(API+'/activos/agregar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ticker:tk,nombre:nm,mercado:mkt})});
    const d=await r.json();
    if(d.ok){
      res.className='add-result ok';
      res.innerHTML=`${d.mensaje}<br><small>${d.dias_descargados} dias &mdash; <a href="${d.yahoo_url}" target="_blank" style="color:var(--green)">Ver en Yahoo Finance</a></small>`;
      if(!allTickers.includes(tk)){allTickers.push(tk);NM[tk]=nm;}
      populateSel(allTickers);cache={};
      document.getElementById('add-tk').value='';document.getElementById('add-nm').value='';
      allLoaded=false;
    }else{res.className='add-result err';res.textContent=d.error;}
  }catch(e){res.className='add-result err';res.textContent='Error de red: '+e.message;}
  btn.disabled=false;btn.innerHTML='&#x2B07; Descargar y agregar';
}

async function loadAll(){
  allLoaded=true;
  try{
    const d=await fno('/activos');const activos=d.activos||[];
    document.getElementById('all-wrap').innerHTML=`<div class="assets-grid">${
      activos.map(a=>`<div class="asset-card">
        <div class="asset-tk">${a.ticker||a}</div>
        <div class="asset-nm">${a.nombre||NM[a.ticker||a]||a}</div>
        <div class="asset-inf">
          <span style="color:var(--txt3)">${a.dias||''} dias</span>
          <a href="${YF+(a.ticker||a)}" target="_blank" class="yfl">YF &#x2197;</a>
        </div></div>`).join('')
    }</div>`;
  }catch(e){document.getElementById('all-wrap').innerHTML=`<p style="color:var(--red);padding:14px">${e.message}</p>`;}
}

async function loadRep(){
  document.getElementById('rep-body').style.display='block';
  document.getElementById('rep-txt').textContent='Cargando...';
  try{const r=await fetch(API+'/reporte/txt');document.getElementById('rep-txt').textContent=await r.text();}
  catch(e){document.getElementById('rep-txt').textContent='Error: '+e.message;}
}

let currentUser=null;
function authTab(t){
  document.getElementById('auth-login').style.display=t==='login'?'block':'none';
  document.getElementById('auth-reg').style.display=t==='reg'?'block':'none';
  document.getElementById('tab-login').className=t==='login'?'act':'';
  document.getElementById('tab-reg').className=t==='reg'?'act':'';
}
function requireAuth(action){
  if(currentUser)return true;
  nav(document.getElementById('nav-auth'),'auth');
  const msg=document.getElementById('auth-msg');
  msg.className='add-result err';msg.style.display='block';
  msg.innerHTML=`Debes <b>iniciar sesion</b> para ${action}.`;
  return false;
}
async function doLogin(){
  const u=document.getElementById('l-user').value.trim(),p=document.getElementById('l-pass').value;
  const msg=document.getElementById('auth-msg');
  if(!u||!p){msg.className='add-result err';msg.style.display='block';msg.textContent='Completa ambos campos.';return;}
  try{
    const r=await fetch(API+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({username:u,password:p})});
    const d=await r.json();
    if(d.ok){msg.className='add-result ok';msg.style.display='block';msg.innerHTML='Bienvenido, <b>'+d.username+'</b>';currentUser=d;updateUserUI();
      setTimeout(()=>nav(document.querySelector('.nav-item'),'ov'),800);
    }else{msg.className='add-result err';msg.style.display='block';msg.textContent=d.error;}
  }catch(e){msg.className='add-result err';msg.style.display='block';msg.textContent=e.message;}
}
async function doRegister(){
  const u=document.getElementById('r-user').value.trim(),e=document.getElementById('r-email').value.trim(),p=document.getElementById('r-pass').value;
  const msg=document.getElementById('auth-msg');
  if(!u||!e||!p){msg.className='add-result err';msg.style.display='block';msg.textContent='Completa todos los campos.';return;}
  try{
    const r=await fetch(API+'/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,email:e,password:p})});
    const d=await r.json();
    if(d.ok){msg.className='add-result ok';msg.style.display='block';msg.innerHTML='Cuenta creada. Ahora inicia sesion.';authTab('login');}
    else{msg.className='add-result err';msg.style.display='block';msg.textContent=d.error;}
  }catch(er){msg.className='add-result err';msg.style.display='block';msg.textContent=er.message;}
}
async function doLogout(){
  try{await fetch(API+'/auth/logout',{method:'POST',credentials:'include'});}catch{}
  currentUser=null;updateUserUI();
}
async function checkAuth(){
  try{const r=await fetch(API+'/auth/me',{credentials:'include'});if(r.ok){currentUser=await r.json();updateUserUI();}}catch{}
}
function updateUserUI(){
  const bar=document.getElementById('user-bar');
  const authBtn=document.getElementById('nav-auth');
  const adminNav=document.getElementById('admin-nav');
  if(currentUser){
    bar.style.display='flex';document.getElementById('uname').textContent=currentUser.username;
    document.getElementById('sim-no-auth').style.display='none';
    document.getElementById('sim-auth').style.display='block';
    authBtn.innerHTML='<span class="nav-icon">&#x1F464;</span> '+currentUser.username;
    authBtn.style.color='var(--green)';
    adminNav.style.display=currentUser.username==='admin'?'block':'none';
  }else{
    bar.style.display='none';
    document.getElementById('sim-no-auth').style.display='block';
    document.getElementById('sim-auth').style.display='none';
    authBtn.innerHTML='<span class="nav-icon">&#x1F464;</span> Iniciar Sesion';
    authBtn.style.color='';adminNav.style.display='none';
  }
}
async function loadAdmin(){
  if(!currentUser||currentUser.username!=='admin')return;
  try{
    const d=await fetch(API+'/admin/usuarios',{credentials:'include'}).then(r=>r.json());
    const users=d.usuarios||[];
    document.getElementById('adm-users').textContent=users.length;
    document.getElementById('adm-ops').textContent=d.total_transacciones||0;
    document.getElementById('adm-user-list').innerHTML=users.length?
      `<div class="table-wrap"><table><thead><tr><th>#</th><th>Usuario</th><th>Email</th><th>Saldo USD</th><th>Posiciones</th><th>Registrado</th></tr></thead><tbody>`+
      users.map((u,i)=>`<tr><td style="color:var(--txt3)">${i+1}</td>
        <td><b style="color:var(--acc)">${u.username}</b>${u.username==='admin'?' <span class="admin-badge">ADMIN</span>':''}</td>
        <td style="color:var(--txt3)">${u.email}</td>
        <td class="mono">${(u.saldo_usd||0).toLocaleString('en-US',{minimumFractionDigits:2})}</td>
        <td class="mono">${u.posiciones||0}</td>
        <td style="font-size:11px;color:var(--txt3)">${(u.creado_en||'').slice(0,10)}</td></tr>`).join('')+
      '</tbody></table></div>':
      '<p style="color:var(--txt3);padding:14px">No hay usuarios registrados.</p>';
  }catch{
    document.getElementById('adm-users').textContent='1+';
    document.getElementById('adm-user-list').innerHTML='<p style="color:var(--txt3);padding:14px">Endpoint admin no disponible aun.</p>';
  }
}
let tasaUsdCop=4250;
async function loadTasa(){
  try{
    const d=await fno('/monedas/tasa');tasaUsdCop=d.usd_cop||4250;
    document.getElementById('fx-usd').textContent='$'+tasaUsdCop.toLocaleString('es-CO',{minimumFractionDigits:2});
    document.getElementById('fx-cop').textContent=tasaUsdCop.toLocaleString('es-CO',{minimumFractionDigits:2});
    document.getElementById('fx-cop-usd').textContent='$'+(d.cop_usd||0).toFixed(8);
    document.getElementById('fx-cop2').textContent=(d.cop_usd||0).toFixed(8);
    convertir('usd');
  }catch{document.getElementById('fx-usd').textContent='Error';}
}
function convertir(from){
  if(from==='usd'){const usd=+document.getElementById('conv-usd').value||0;document.getElementById('conv-cop').value=Math.round(usd*tasaUsdCop);}
  else{const cop=+document.getElementById('conv-cop').value||0;document.getElementById('conv-usd').value=(cop/tasaUsdCop).toFixed(2);}
}
let leccionesLoaded=false;
async function loadLecciones(){
  if(leccionesLoaded)return;leccionesLoaded=true;
  try{
    const d=await fno('/academia/lecciones');
    document.getElementById('lecciones-wrap').innerHTML=(d.lecciones||[]).map(l=>`
      <div class="lesson-card" onclick="openLeccion(${l.id})">
        <div class="lesson-icon">${l.icono}</div>
        <div class="lesson-title">${l.titulo}</div>
        <div class="lesson-meta"><span>${l.categoria}</span><span>${l.duracion}</span></div>
      </div>`).join('');
  }catch(e){document.getElementById('lecciones-wrap').innerHTML=`<p style="color:var(--red)">${e.message}</p>`;}
}
async function openLeccion(id){
  document.getElementById('lecciones-wrap').style.display='none';
  document.getElementById('leccion-detail').style.display='block';
  try{
    const d=await fno('/academia/leccion?id='+id);
    let html=d.contenido||'';
    html=html.replace(/^### (.+)$/gm,'<h3>$1</h3>').replace(/^## (.+)$/gm,'<h2>$1</h2>');
    html=html.replace(/^> (.+)$/gm,'<blockquote>$1</blockquote>');
    html=html.replace(/\\*\\*(.+?)\\*\\*/g,'<b>$1</b>');
    html=html.replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g,'<a href="$2" target="_blank">$1</a>');
    html=html.replace(/^- (.+)$/gm,'<li>$1</li>');
    html=html.replace(/```([\\s\\S]*?)```/g,'<pre>$1</pre>');
    html=html.replace(/`([^`]+)`/g,'<code>$1</code>');
    html=html.replace(/\\n\\n/g,'<br>');
    document.getElementById('leccion-body').innerHTML=`<h2>${d.icono} ${d.titulo}</h2><div class="lesson-meta" style="margin-bottom:16px"><span>${d.categoria}</span><span>${d.duracion}</span></div>`+html;
  }catch(e){document.getElementById('leccion-body').innerHTML=`<p style="color:var(--red)">${e.message}</p>`;}
}
function backToLessons(){
  document.getElementById('lecciones-wrap').style.display='grid';
  document.getElementById('leccion-detail').style.display='none';
}
async function loadSim(){
  if(!requireAuth('usar el simulador'))return;
  const sel=document.getElementById('sim-tk');
  if(sel&&!sel.options.length)sel.innerHTML=allTickers.map(t=>`<option value="${t}">${t}</option>`).join('');
  try{
    const d=await fetch(API+'/simulador/portafolio',{credentials:'include'}).then(r=>r.json());
    document.getElementById('sim-usd').textContent='$'+(d.saldo_usd||0).toLocaleString('en-US',{minimumFractionDigits:2});
    document.getElementById('sim-cop').textContent='$'+(d.saldo_cop||0).toLocaleString('es-CO');
    const ps=d.posiciones||[];document.getElementById('sim-pos').textContent=ps.length;
    document.getElementById('sim-positions').innerHTML=ps.length?
      `<div class="table-wrap"><table><thead><tr><th>Ticker</th><th>Cantidad</th><th>Precio Prom.</th><th>Invertido</th><th>Yahoo</th></tr></thead><tbody>`+
      ps.map(p=>`<tr><td><b style="color:var(--acc)">${p.ticker}</b></td><td class="mono">${p.cantidad}</td><td class="mono">${p.precio_promedio.toFixed(2)}</td><td class="mono">${p.total_invertido.toFixed(2)}</td><td><a href="${YF+p.ticker}" target="_blank" class="yfl">YF &#x2197;</a></td></tr>`).join('')+
      '</tbody></table></div>':
      '<p style="color:var(--txt3);padding:14px">No tienes posiciones abiertas.</p>';
    const tx=d.transacciones||[];
    document.getElementById('sim-history').innerHTML=tx.length?
      `<div class="table-wrap"><table><thead><tr><th>Tipo</th><th>Ticker</th><th>Cant.</th><th>Precio</th><th>Total</th><th>Fecha</th></tr></thead><tbody>`+
      tx.map(t=>`<tr><td><span class="badge ${t.tipo==='compra'?'bg':'br'}">${t.tipo}</span></td><td><b>${t.ticker}</b></td><td class="mono">${t.cantidad}</td><td class="mono">${t.precio.toFixed(2)}</td><td class="mono">${t.total.toFixed(2)}</td><td style="font-size:11px;color:var(--txt3)">${t.fecha.slice(0,16).replace('T',' ')}</td></tr>`).join('')+
      '</tbody></table></div>':
      '<p style="color:var(--txt3);padding:14px">Sin transacciones aun.</p>';
  }catch(e){console.error(e);}
}
async function simComprar(){
  if(!requireAuth('comprar activos'))return;
  const tk=document.getElementById('sim-tk').value,qty=+document.getElementById('sim-qty').value;
  const msg=document.getElementById('sim-msg');
  try{
    const r=await fetch(API+'/simulador/comprar',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({ticker:tk,cantidad:qty})});
    const d=await r.json();
    if(d.ok){msg.className='add-result ok';msg.style.display='block';msg.textContent=d.mensaje;loadSim();}
    else{msg.className='add-result err';msg.style.display='block';msg.textContent=d.error;}
  }catch(e){msg.className='add-result err';msg.style.display='block';msg.textContent=e.message;}
}
async function simVender(){
  if(!requireAuth('vender activos'))return;
  const tk=document.getElementById('sim-tk').value,qty=+document.getElementById('sim-qty').value;
  const msg=document.getElementById('sim-msg');
  try{
    const r=await fetch(API+'/simulador/vender',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({ticker:tk,cantidad:qty})});
    const d=await r.json();
    if(d.ok){msg.className='add-result ok';msg.style.display='block';msg.textContent=d.mensaje;loadSim();}
    else{msg.className='add-result err';msg.style.display='block';msg.textContent=d.error;}
  }catch(e){msg.className='add-result err';msg.style.display='block';msg.textContent=e.message;}
}
init();checkAuth();
</script>
</body>
</html>
""")

# ── escribir todo ──────────────────────────────────────────────────
OUT.write_text(existing + JS + JS2 + JS3 + JS4, encoding="utf-8")
size = OUT.stat().st_size
print(f"OK — {OUT} ({size:,} bytes)")
