import React,{useState} from 'react';
export type Run={city:string,h:number,model:string,origin:string,date:string,prediction:number,n:number,rmse:number,mode:string,version:string,trained_at:string,recent_n:number,publishable:boolean,is_archived?:boolean,data_version?:string};
export type Observation={date:string,lst:number|null,valid_fraction:number,valid_pixels:number,total_pixels:number,complete_tiles:boolean};
export type RegionExtra={provinceHistory?:Observation[],provinceScores?:{model:string,h:number,n:number,rmse:number,mae:number}[],runs?:Run[],summerScores?:{group:string,model:string,n:number,rmse:number,pred_min:number,pred_max:number,outside_review_range:number}[]};
const fmt=(n:number)=>Number.isFinite(n)?n.toLocaleString('tr-TR',{maximumFractionDigits:2}):'—';
export function Province({city,region}:{city:string,region:RegionExtra}){
 const history=region.provinceHistory||[],years=Array.from(new Set(history.map(r=>r.date.slice(0,4)))).sort().reverse();
 const [choice,Y]=useState(years[0]||''),[model,M]=useState('LSTM'),[h,H]=useState(2);
 const year=years.includes(choice)?choice:years[0]||'';
 const selected=history.filter(r=>r.date.startsWith(year)),valid=selected.filter(r=>r.lst!==null);
 const run=region.runs?.find(r=>r.mode==='province'&&r.model===model&&r.h===h);
 if(!history.length)return null;
 return <section><div className="row"><h2>{city} · İl ortalaması</h2><select aria-label="İl serisi yılı" value={year} onChange={e=>Y(e.target.value)}>{years.map(y=><option key={y}>{y}</option>)}</select></div>
 <p>MODIS Terra · İl sınırı içindeki geçerli gündüz pikselleri. {year} için {valid.length} / 46 beklenen dönem kalite eşiğini geçti.</p>
 <details><summary>Dönem ölçümleri ve piksel kapsamı</summary><div className="scroll"><table><thead><tr>{['Dönem','LST °C','Geçerli piksel','Toplam piksel','Kapsam'].map(x=><th key={x}>{x}</th>)}</tr></thead><tbody>{selected.map(r=><tr key={r.date}><td>{r.date}</td><td>{r.lst===null?'—':fmt(r.lst)}</td><td>{r.valid_pixels}</td><td>{r.total_pixels}</td><td>%{fmt(100*r.valid_fraction)}{r.complete_tiles?'':' · eksik karo'}</td></tr>)}</tbody></table></div></details>
 <h3>İl ortalaması tahmini</h3><div className="row"><select aria-label="İl tahmin modeli" value={model} onChange={e=>M(e.target.value)}>{['LSTM','XGBoost'].map(m=><option key={m}>{m}</option>)}</select><select aria-label="İl tahmin ufku" value={h} onChange={e=>H(+e.target.value)}>{[1,2,3,4].map(i=><option key={i} value={i}>{i*8} gün</option>)}</select></div>
 {region.provinceScores&&<div className="scroll"><table><thead><tr><th>Model</th><th>n</th><th>MAE °C</th><th>RMSE °C</th></tr></thead><tbody>{region.provinceScores.filter(x=>x.h===h).map(x=><tr key={x.model}><td>{x.model}</td><td>{x.n}</td><td>{fmt(x.mae)}</td><td>{fmt(x.rmse)}</td></tr>)}</tbody></table><small>2024–2025 bağımsız zaman testi; yalnızca bu il ve seçilen ufuk.</small></div>}
 {run?.publishable?<article><strong>{fmt(run.prediction)} °C</strong><p>{run.date<new Date().toISOString().slice(0,10)?'Arşiv tahmini':'Son doğrulanmış veriyle tahmin'} · Hedef {run.date} · Son girdi {run.origin} · Test RMSE {fmt(run.rmse)} °C ({run.n} örnek)</p><small>Son 8 dönemde {run.recent_n} ölçüm · Eğitim {run.trained_at?.slice(0,10)} · Sürüm {run.version?.slice(0,12)}</small></article>:<p>Bu model ve ufuk için yayımlanabilir doğrulanmış tahmin yok.</p>}</section>
}
export function SpatialResults({data}:{data:RegionExtra}){
 const [model,M]=useState('XGBoost');const scores=data.summerScores||[];if(!scores.length)return null;
 return <section><div className="row"><h2>Çok yıllı mekânsal test</h2><select aria-label="Mekânsal test modeli" value={model} onChange={e=>M(e.target.value)}>{Array.from(new Set(scores.map(x=>x.model))).map(x=><option key={x}>{x}</option>)}</select></div><p>Test ili eğitim dışında · Eğitim 2018–2023, test 2024–2025</p><table><thead><tr>{['Grup','n','RMSE °C','Tahmin aralığı °C','İncelenecek'].map(x=><th key={x}>{x}</th>)}</tr></thead><tbody>{scores.filter(x=>x.model===model).map(x=><tr key={x.group}><td>{x.group}</td><td>{x.n}</td><td>{fmt(x.rmse)}</td><td>{fmt(x.pred_min)} … {fmt(x.pred_max)}</td><td>{x.outside_review_range}</td></tr>)}</tbody></table></section>
}
