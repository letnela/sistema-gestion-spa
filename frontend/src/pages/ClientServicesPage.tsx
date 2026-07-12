import {useMemo,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {http} from '../api/http';
import {Link} from 'react-router-dom';
import {Clock,Percent,Search,Sparkles,CalendarPlus} from 'lucide-react';

export function ClientServicesPage(){
 const [search,setSearch]=useState('');
 const [category,setCategory]=useState('TODOS');
 const {data:services=[]}=useQuery({queryKey:['client-services'],queryFn:async()=>(await http.get('/client-portal/catalog/services')).data.data});
 const {data:promos=[]}=useQuery({queryKey:['client-promotions'],queryFn:async()=>(await http.get('/client-portal/catalog/promotions')).data.data});
 const categories=useMemo(()=>['TODOS',...Array.from(new Set(services.map((s:any)=>s.categoria_nombre).filter(Boolean)))],[services]);
 const filtered=useMemo(()=>services.filter((s:any)=>{
   const q=search.trim().toLowerCase();
   return (category==='TODOS'||s.categoria_nombre===category)&&(!q||`${s.nombre} ${s.descripcion||''} ${s.categoria_nombre||''}`.toLowerCase().includes(q));
 }),[services,search,category]);
 return <div className="space-y-7">
  <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-violet-700 via-fuchsia-600 to-rose-500 p-7 text-white shadow-xl md:p-10">
   <div className="max-w-2xl"><span className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-sm font-semibold"><Sparkles size={16}/> Experiencias diseñadas para ti</span><h1 className="mt-4 text-3xl font-black md:text-5xl">Tu mejor versión empieza aquí</h1><p className="mt-3 text-white/85 md:text-lg">Explora el catálogo, compara duración y precio, y reserva con el profesional ideal.</p><Link className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 font-bold text-violet-700 shadow-lg hover:bg-violet-50" to="/cliente/agendar"><CalendarPlus size={19}/>Agendar ahora</Link></div>
  </section>
  {promos.length>0&&<section><div className="mb-3 flex items-center gap-2"><Percent className="text-fuchsia-600"/><h2 className="text-xl font-black">Promociones vigentes</h2></div><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{promos.map((p:any)=><div className="card relative overflow-hidden border-fuchsia-200 bg-gradient-to-br from-fuchsia-50 to-violet-50 dark:from-fuchsia-950/40 dark:to-violet-950/30" key={p.id}><div className="absolute -right-8 -top-8 h-28 w-28 rounded-full bg-fuchsia-500/10"/><span className="inline-flex rounded-full bg-fuchsia-600 px-3 py-1 text-sm font-black text-white">{Number(p.porcentaje_descuento)}% OFF</span><h3 className="mt-3 text-lg font-black">{p.nombre}</h3><p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{p.descripcion||'Promoción especial por tiempo limitado'}</p><p className="mt-4 text-xs font-medium text-slate-500">Válida hasta {p.fecha_fin}</p></div>)}</div></section>}
  <section className="space-y-4"><div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between"><div><h2 className="text-2xl font-black">Servicios</h2><p className="text-slate-500">{filtered.length} experiencias disponibles</p></div><div className="relative w-full lg:w-80"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18}/><input className="field pl-10" placeholder="Buscar servicio..." value={search} onChange={e=>setSearch(e.target.value)}/></div></div>
   <div className="flex gap-2 overflow-x-auto pb-1">{categories.map((c:any)=><button key={c} onClick={()=>setCategory(c)} className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-bold ${category===c?'bg-violet-600 text-white':'bg-white text-slate-600 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-200 dark:ring-slate-700'}`}>{c==='TODOS'?'Todos':c}</button>)}</div>
   <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">{filtered.map((s:any)=><article className="group overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-xl dark:border-slate-800 dark:bg-slate-900" key={s.id}><div className="relative h-48 overflow-hidden bg-slate-100"><img src={s.imagen_url||'/images/services/category-1.svg'} alt={s.nombre} className="h-full w-full object-cover transition duration-500 group-hover:scale-105"/><span className="absolute left-4 top-4 rounded-full bg-white/90 px-3 py-1 text-xs font-black text-violet-700 backdrop-blur">{s.categoria_nombre||'Servicio'}</span></div><div className="p-5"><h3 className="text-lg font-black">{s.nombre}</h3><p className="mt-2 min-h-10 text-sm leading-5 text-slate-500">{s.descripcion||'Servicio profesional personalizado.'}</p><div className="mt-5 flex items-center justify-between border-t border-slate-100 pt-4 dark:border-slate-800"><span className="flex items-center gap-1.5 text-sm font-semibold text-slate-500"><Clock size={16}/>{s.duracion_minutos} min</span><span className="text-xl font-black text-violet-700">S/ {Number(s.precio).toFixed(2)}</span></div><Link className="btn-primary mt-4 w-full justify-center" to={`/cliente/agendar?servicio=${s.id}`}>Reservar este servicio</Link></div></article>)}</div>
   {filtered.length===0&&<div className="card py-12 text-center text-slate-500">No encontramos servicios con esos filtros.</div>}
  </section>
 </div>
}
