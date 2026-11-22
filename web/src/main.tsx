import React,{useState,useEffect} from 'react';
import {createRoot} from 'react-dom/client';
import raw from './snapshot.json';
import './style.css';
import {Province, SpatialResults, type RegionExtra,type Run} from './Province';
type Cell={date:string,lat:number,lon:number,lst:number,ndvi:number,ndbi:number};
type Score={city:string,model:string,mae:number,rmse:number,r2:number|null,n:number,h?:number,group?:string,mode?:string};
type Region=RegionExtra & {cells?:Cell[],candidates?:number,spatial?:Score[],history?:{date:string,lst:number|null}[],location?:{lat:number,lon:number},scores?:Score[],future?:{date:string,h:number,origin:string,mode:string,model:string,prediction:number}[]};
type Feature={properties:{name:string},geometry:{type:string,coordinates:unknown}};
const atlas=raw as unknown as {features:Feature[],regions:Record<string,Region>};
const names=atlas.features.map(f=>f.properties.name).sort((a,b)=>a.localeCompare(b,'tr'));

function shape(f:Feature){
 const polys=(f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates) as number[][][][];
 return polys.flatMap(p=>p.map(r=>r.map(([x,y],i)=>(i?'L':'M')+((x-25.4)*36).toFixed(1)+' '+((42.4-y)*45).toFixed(1)).join('')+'Z')).join('');
}
const shapes=atlas.features.map(f=>({name:f.properties.name,d:shape(f)}));
const fmt=(v:number|null|undefined)=>v==null?'—':v.toLocaleString('tr-TR',{maximumFractionDigits:2});
function Table({rows}:{rows:Score[]}){return <div className="scroll"><table><thead><tr>{['Model','Grup','n','MAE (°C)','RMSE (°C)','R²'].map(s=><th key={s}>{s}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i}><td>{r.model}</td><td>{r.group||'—'}</td><td>{r.n}</td><td>{fmt(r.mae)}</td><td>{fmt(r.rmse)}</td><td>{fmt(r.r2)}</td></tr>)}</tbody></table></div>}
function History({data}:{data:Region}) {
 const [year,Y]=useState(2025);
 const available=new Map((data.history||[]).map(r=>[r.date,r.lst]));
 const rows=Array.from({length:46},(_,i)=>{const date=new Date(Date.UTC(year,0,1+i*8)).toISOString().slice(0,10);return {date,lst:available.get(date)??null}});
 const earlier=(data.history||[]).filter(i=>i.date.startsWith(String(year-1)));
 const deltas=rows.flatMap(r=>{const t=earlier.find(q=>Math.round((Date.parse(r.date)-Date.parse(year+"-01-01"))/86400000)===Math.round((Date.parse(q.date)-Date.parse((year-1)+"-01-01"))/86400000));return r.lst!=null&&t?.lst!=null?[r.lst-t.lst]:[]});
 const years=Array.from(new Set((data.history||[]).map(i=>+i.date.slice(0,4)))).sort();
 const vals=rows.flatMap(i=>i.lst===null?[]:[i.lst]);
 const lo=Math.floor(Math.min(...vals)/10)*10,hi=Math.max(lo+10,Math.ceil(Math.max(...vals)/10)*10);
 const px=(i:number)=>42+i*550/45,py=(v:number)=>115-(v-lo)*90/(hi-lo);
 return <section><div className="row"><h2>Geçmiş yüzey sıcaklığı</h2><select aria-label="Gözlem yılı" value={year} onChange={e=>Y(+e.target.value)}>{years.map(y=><option key={y}>{y}</option>)}</select></div><p>MODIS gündüz · {data.location?.lat}° K, {data.location?.lon}° D · Tek uydu pikseli</p>{vals.length>0&&<svg viewBox="0 0 620 145" role="img" aria-label="Sekiz günlük sıcaklık serisi">{[lo,(lo+hi)/2,hi].map(v=><g key={v}><text x="0" y={py(v)+4}>{fmt(v)}°</text><line x1="38" x2="597" y1={py(v)} y2={py(v)} stroke="#dce4de"/></g>)}{rows.map((r,i)=>r.lst===null?null:<g key={r.date}>{i>0&&rows[i-1].lst!==null&&<line x1={px(i-1)} x2={px(i)} y1={py(rows[i-1].lst!)} y2={py(r.lst)} stroke="#08796e" strokeWidth="2"/>}<circle cx={px(i)} cy={py(r.lst)} r="3" fill="#08796e"><title>{r.date} · {fmt(r.lst)} °C</title></circle></g>)}<text x="40" y="138">Ocak</text><text x="550" y="138">Aralık</text></svg>}<small>{rows.length} dönemin {vals.length} tanesinde kalite eşiğini geçen ölçüm var. {deltas.length>0&&<>Önceki yılla ortak {deltas.length} dönemde ortalama fark {fmt(deltas.reduce((a,b)=>a+b,0)/deltas.length)} °C.</>}</small></section>
}
function App(){
 const [city,C]=useState('Antalya'),[h,H]=useState(2),[mode,M]=useState("uni"),[region,R]=useState<Region>(atlas.regions.Antalya),[error,E]=useState(''),[busy,B]=useState(false);
 useEffect(()=>{if(location.protocol==='file:'||location.port==='5173'){R(atlas.regions[city]||{});return}const ctrl=new AbortController();B(true);E('');fetch('/api/iller/'+encodeURIComponent(city),{signal:ctrl.signal}).then(r=>{if(!r.ok)throw Error();return r.json()}).then(data=>{R(data);B(false)}).catch(()=>{if(!ctrl.signal.aborted){E('İl verisi API üzerinden yüklenemedi.');B(false)}});return()=>ctrl.abort()},[city]);
 const offline=location.protocol==='file:'||location.port==='5173';
 const [layers,L]=useState<Run[]>(()=>offline?Object.values(atlas.regions).flatMap(r=>(r.runs||[]).filter(x=>x.mode==='province'&&x.publishable)):[]);
 const [layerModel,LM]=useState('LSTM'),[layerH,LH]=useState(2),[layerError,LE]=useState(false);
 useEffect(()=>{if(offline)return;const ctrl=new AbortController();fetch('/api/tahmin-katmani',{signal:ctrl.signal}).then(r=>{if(!r.ok)throw Error();return r.json()}).then(L).catch(()=>{if(!ctrl.signal.aborted)LE(true)});return()=>ctrl.abort()},[offline]);
 const layer=layers.filter(x=>x.model===layerModel&&x.h===layerH);
 const targets=Array.from(new Set(layer.map(x=>x.date))).sort().reverse();
 const [target,T]=useState('');const selected=targets.includes(target)?target:targets[0];
 const values=new Map(layer.filter(x=>x.date===selected).map(x=>[x.city,x.prediction]));
 const cells=region.cells||[],xs=cells.map(r=>r.lon),ys=cells.map(r=>r.lat);
 const future=(region.future||[]).filter(x=>x.h===h&&x.mode===mode);
 return <main><header><span>UYDU GÖZLEMLERİ</span><h1>Yüzey Sıcaklığı Atlası</h1><p>Türkiye’de arazi yüzey sıcaklığının mekânsal dağılımı ve sekiz günlük dönem tahminleri.</p></header><section><div className="row"><h2>Çalışma alanları</h2><select aria-label="İl seçimi" value={city} onChange={e=>C(e.target.value)}>{names.map(n=><option key={n}>{n}</option>)}</select></div><svg viewBox="0 0 720 305" role="img" aria-label="İl ortalaması tahmin katmanı">{shapes.map(f=><path key={f.name} d={f.d} fill={values.has(f.name)?'hsl('+Math.max(0,Math.min(230,200-4*values.get(f.name)!))+' 60% 45%)':'#dbe5de'} stroke={f.name===city?'#122a2c':'#fff'} strokeWidth={f.name===city?2:.8} onClick={()=>C(f.name)}><title>{f.name} · {values.has(f.name)?fmt(values.get(f.name))+" °C":"Veri yok"}</title></path>)}</svg><div className="row"><select aria-label="Harita modeli" value={layerModel} onChange={e=>LM(e.target.value)}><option>LSTM</option><option>XGBoost</option></select><select aria-label="Harita ufku" value={layerH} onChange={e=>LH(+e.target.value)}>{[1,2,3,4].map(i=><option key={i} value={i}>{i*8} gün</option>)}</select><select aria-label="Harita hedef dönemi" value={selected||''} onChange={e=>T(e.target.value)}>{targets.map(t=><option key={t}>{t}</option>)}</select></div><small>{layerError?'Tahmin katmanı yüklenemedi.':values.size+' ilde doğrulanmış tahmin · Gri alanlarda yayımlanmış değer yok.'} Renk ölçeği soğuktan sıcağa maviden turuncuya geçer.</small></section><h2 className="city">{city}</h2>{!busy&&!error&&<><Province key={city} city={city} region={region}/><SpatialResults data={region}/></>}{busy?<p>Yükleniyor…</p>:error?<p>{error}</p>:!region.history?<section>Bu il için tek piksel pilot deneyi bulunmuyor.</section>:<>
 <History data={region}/><section><div className="row"><h2>Dönem tahmini</h2><select aria-label="Girdi türü" value={mode} onChange={e=>M(e.target.value)}><option value="uni">Geçmiş LST · 2003 sonrası</option><option value="common">Geçmiş LST · Ortak 2018 sonrası</option>{region.scores?.some(r=>r.mode==="multi")&&<option value="multi">LST + çevresel veriler</option>}</select><select value={h} aria-label="Tahmin ufku" onChange={e=>H(+e.target.value)}>{[1,2,3,4].map(i=><option key={i} value={i}>{8*i} günlük ufuk</option>)}</select></div><p>Arşiv deneyi · Son girdi döneminin başlangıcı {future[0]?.origin||'—'}. Hedef dönem {future[0]?.date||'—'} itibarıyla başlar.</p><div className="cards">{future.map(r=><article key={r.model}><small>{r.model}</small><strong>{fmt(r.prediction)} °C</strong>{r.model!=="SeasonalNaive"&&<small>{region.runs?.find(v=>v.mode===mode&&v.model===r.model)?.trained_at?.slice(0,10)} · {region.runs?.find(v=>v.mode===mode&&v.model===r.model)?.version?.slice(0,12)}</small>}</article>)}</div><h3>2024–2025 bağımsız test sonuçları</h3><Table rows={(region.scores||[]).filter(r=>r.h===h&&r.mode===mode)}/></section>
 <section><h2>300 m hücrelerde Landsat gözlemi</h2><p>{cells[0]?.date} · Geçerli hücre {cells.length} / {region.candidates}</p>{cells.length>0&&<svg viewBox="0 0 320 200" style={{maxHeight:240}} role="img" aria-label="Pilot örnekleme alanının sıcaklık haritası">{cells.map((r,i)=><rect key={i} x={60+180*(r.lon-Math.min(...xs))/(Math.max(...xs)-Math.min(...xs)||1)} y={8+178*(Math.max(...ys)-r.lat)/(Math.max(...ys)-Math.min(...ys)||1)} width="8" height="8" fill={'hsl('+Math.max(0,Math.min(200,220-4.5*r.lst))+' 66% 41%)'}><title>{fmt(r.lst)} °C · NDVI {fmt(r.ndvi)} · NDBI {fmt(r.ndbi)}</title></rect>)}</svg>}<small>Renk ölçeği <b className="ramp"/> 10–48 °C · Hücre üzerine gelerek ölçümü görebilirsin.</small><h3>2023 tek-sahne arşiv testi · {city} eğitim dışında</h3><p>Bu tablo ilk deneyin hata analizini içerir. Güncel çok yıllı test yukarıda gösterilir.</p><Table rows={region.spatial||[]}/><small>A = NDVI, NDBI · B = A + rakım ve eğim</small></section></>}<footer>Landsat Collection 2 · Sentinel-2 L2A · MODIS Terra · Natural Earth</footer></main>
}
createRoot(document.getElementById('root')!).render(<App/>);
