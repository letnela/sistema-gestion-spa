import{Link}from'react-router-dom';import{useState}from'react';import{useQuery}from'@tanstack/react-query';import{http}from'../api/http';import{Scissors,Sparkles,Clock,MapPin,Phone,Instagram,Check,Star,Eye}from'lucide-react';import{ChatWidget}from'../components/ChatWidget';import{Modal}from'../components/Modal';

const FALLBACK_IMG='https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=800&q=80';

const RAZONES=[
 'Profesionales certificados con años de experiencia',
 'Productos premium, seguros para cada tipo de cabello',
 'Reserva tu cita en línea, sin llamadas ni esperas',
 'Portal de cliente: historial, compras y comprobantes en un solo lugar',
];

type Detalle={tipo:'servicio'|'producto';item:any};

export function LandingPage(){
 const{data:servicios=[],isLoading}=useQuery({queryKey:['public-services'],queryFn:async()=>(await http.get('/public/services')).data.data});
 const{data:productos=[],isLoading:isLoadingProductos}=useQuery({queryKey:['public-products'],queryFn:async()=>(await http.get('/public/products')).data.data});
 const[detalle,setDetalle]=useState<Detalle|null>(null);
 const ctaHref=detalle?.tipo==='servicio'
  ?`/registro-cliente?next=${encodeURIComponent(`/cliente/agendar?servicio=${detalle.item.id}`)}`
  :`/registro-cliente?next=${encodeURIComponent('/cliente/tienda')}`;
 return <div className="bg-white dark:bg-slate-950">

  {/* Header */}
  <header className="sticky top-0 z-40 border-b border-white/10 bg-slate-950/90 backdrop-blur">
   <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
    <div className="flex items-center gap-2 text-white"><div className="grid h-9 w-9 place-items-center rounded-xl bg-violet-600"><Scissors size={18}/></div><div><p className="text-[10px] font-black uppercase tracking-[.25em] text-violet-300">Elegance</p><p className="-mt-0.5 text-sm font-bold">Salon Manager</p></div></div>
    <nav className="hidden items-center gap-8 text-sm font-semibold text-white/70 md:flex"><a href="#nosotros" className="hover:text-white">Nosotros</a><a href="#servicios" className="hover:text-white">Servicios</a><a href="#productos" className="hover:text-white">Tienda</a><a href="#contacto" className="hover:text-white">Contacto</a></nav>
    <div className="flex items-center gap-2"><Link to="/login" className="rounded-xl px-4 py-2 text-sm font-bold text-white hover:bg-white/10">Iniciar sesión</Link><Link to="/registro-cliente" className="rounded-xl bg-white px-4 py-2 text-sm font-black text-slate-950">Reservar cita</Link></div>
   </div>
  </header>

  {/* Hero */}
  <section className="relative overflow-hidden bg-gradient-to-br from-violet-950 via-slate-950 to-fuchsia-950 px-5 py-20 text-white sm:py-28">
   <img className="absolute inset-0 h-full w-full object-cover opacity-25" src="https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=1800&q=80" alt=""/>
   <div className="relative mx-auto max-w-3xl text-center">
    <span className="eyebrow mx-auto"><Sparkles size={14}/> Salón de belleza en Miraflores</span>
    <h1 className="mt-6 text-4xl font-black leading-[1.05] sm:text-6xl">Belleza que se nota,<br className="hidden sm:block"/> cuidado que se siente</h1>
    <p className="mx-auto mt-5 max-w-xl text-lg text-white/75">Corte, color, spa capilar y maquillaje en un espacio pensado para que cada visita sea un momento solo tuyo.</p>
    <div className="mt-8 flex flex-wrap items-center justify-center gap-3"><Link to="/registro-cliente" className="rounded-2xl bg-white px-6 py-3.5 font-black text-slate-950 shadow-xl">Crear cuenta y reservar</Link><Link to="/login" className="rounded-2xl border border-white/30 px-6 py-3.5 font-bold text-white hover:bg-white/10">Ya tengo cuenta</Link></div>
    <div className="mt-14 grid grid-cols-3 gap-6 border-t border-white/10 pt-8 text-center"><div><p className="text-3xl font-black">12+</p><p className="mt-1 text-xs uppercase tracking-wider text-white/60">Años de experiencia</p></div><div><p className="text-3xl font-black">5</p><p className="mt-1 text-xs uppercase tracking-wider text-white/60">Estilistas especializados</p></div><div><p className="text-3xl font-black">4.9<Star className="mb-1 ml-1 inline text-amber-400" size={18} fill="currentColor"/></p><p className="mt-1 text-xs uppercase tracking-wider text-white/60">Calificación de clientas</p></div></div>
   </div>
  </section>

  

  {/* Servicios */}
  <section id="servicios" className="bg-slate-50 px-5 py-20 dark:bg-slate-900/40">
   <div className="mx-auto max-w-6xl">
    <div className="mx-auto max-w-xl text-center"><span className="eyebrow border-slate-200 bg-white text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">Servicios</span><h2 className="section-title mt-4">Lo que hacemos mejor</h2><p className="muted mt-3">Un catálogo completo pensado para acompañarte en cada etapa de tu cuidado personal.</p></div>
    <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
     {isLoading?Array.from({length:4}).map((_,i)=><div key={i} className="card h-56 animate-pulse bg-slate-100 dark:bg-slate-800"/>):
      servicios.length===0?<p className="col-span-full text-center text-slate-500">Todavía no hay servicios publicados.</p>:
      servicios.slice(0,8).map((s:any)=><button key={s.id} onClick={()=>setDetalle({tipo:'servicio',item:s})} className="product-card text-left"><div className="relative aspect-[4/3] overflow-hidden bg-slate-100"><img src={s.imagen_url||FALLBACK_IMG} onError={e=>{(e.currentTarget as HTMLImageElement).src=FALLBACK_IMG}} className="h-full w-full object-cover transition group-hover:scale-105" alt={s.nombre}/><span className="absolute inset-x-0 bottom-0 flex items-center justify-center gap-1.5 bg-slate-950/70 py-2 text-xs font-bold text-white opacity-0 backdrop-blur transition hover:opacity-100"><Eye size={13}/>Ver más</span></div><div className="p-4"><p className="text-xs font-bold uppercase tracking-wider text-violet-600">{s.categoria_nombre||'Servicio'}</p><h3 className="mt-1 font-black leading-5">{s.nombre}</h3><div className="mt-3 flex items-center justify-between text-sm"><span className="flex items-center gap-1 text-slate-500"><Clock size={13}/>{s.duracion_minutos} min</span><b className="text-violet-700">S/ {Number(s.precio).toFixed(2)}</b></div></div></button>)}
    </div>
    <div className="mt-10 text-center"><Link to="/registro-cliente" className="btn-primary mx-auto !px-7 !py-3">Ver catálogo completo y reservar</Link></div>
   </div>
  </section>

  {/* Productos */}
  <section id="productos" className="mx-auto max-w-6xl px-5 py-20">
   <div className="mx-auto max-w-xl text-center"><span className="eyebrow border-slate-200 bg-slate-100 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">Tienda</span><h2 className="section-title mt-4">Productos destacados</h2><p className="muted mt-3">Lleva el cuidado profesional a casa. Disponibles para recojo en el salón.</p></div>
   <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
    {isLoadingProductos?Array.from({length:4}).map((_,i)=><div key={i} className="card h-56 animate-pulse bg-slate-100 dark:bg-slate-800"/>):
     productos.length===0?<p className="col-span-full text-center text-slate-500">Todavía no hay productos publicados.</p>:
     productos.slice(0,8).map((p:any)=><button key={p.id} onClick={()=>setDetalle({tipo:'producto',item:p})} className="product-card text-left"><div className="relative aspect-[4/3] overflow-hidden bg-slate-100"><img src={p.imagen_url||FALLBACK_IMG} onError={e=>{(e.currentTarget as HTMLImageElement).src=FALLBACK_IMG}} className="h-full w-full object-cover" alt={p.nombre}/><span className="absolute inset-x-0 bottom-0 flex items-center justify-center gap-1.5 bg-slate-950/70 py-2 text-xs font-bold text-white opacity-0 backdrop-blur transition hover:opacity-100"><Eye size={13}/>Ver más</span></div><div className="p-4"><p className="text-xs font-bold uppercase tracking-wider text-violet-600">{p.marca||p.categoria_nombre||'Profesional'}</p><h3 className="mt-1 line-clamp-2 min-h-10 font-black leading-5">{p.nombre}</h3><div className="mt-3 text-right"><b className="text-violet-700">S/ {Number(p.precio).toFixed(2)}</b></div></div></button>)}
   </div>
   <div className="mt-10 text-center"><Link to="/registro-cliente" className="btn-secondary mx-auto !px-7 !py-3">Ver tienda completa</Link></div>
  </section>

  {/* Contacto */}
  <section id="contacto" className="mx-auto max-w-6xl px-5 py-20">
   <div className="grid gap-8 rounded-[2rem] bg-slate-950 p-10 text-white sm:p-14 lg:grid-cols-[1.2fr_1fr]">
    <div><h2 className="text-3xl font-black">Visítanos o reserva en línea</h2><p className="mt-3 max-w-md text-white/70">Atendemos con cita previa para asegurar tu horario. Crea tu cuenta de cliente y reserva en menos de un minuto.</p><Link to="/registro-cliente" className="btn-primary mt-6 inline-flex !px-6 !py-3">Reservar mi cita</Link></div>
    <div className="space-y-4 text-sm">
     <div className="flex items-start gap-3"><MapPin size={18} className="mt-0.5 text-violet-300"/><span>Av. Larco 1234, Miraflores, Lima</span></div>
     <div className="flex items-start gap-3"><Clock size={18} className="mt-0.5 text-violet-300"/><span>Lunes a sábado · 9:00 a. m. – 8:00 p. m.</span></div>
     <div className="flex items-start gap-3"><Phone size={18} className="mt-0.5 text-violet-300"/><span>+51 987 410 201</span></div>
     <div className="flex items-start gap-3"><Instagram size={18} className="mt-0.5 text-violet-300"/><span>@elegance.salon</span></div>
    </div>
   </div>
  </section>

  <footer className="border-t border-slate-100 px-5 py-8 text-center text-sm text-slate-400 dark:border-slate-900">© {new Date().getFullYear()} Elegance Salon Manager · <Link to="/login" className="underline">Acceso para el equipo</Link></footer>
  <Modal open={!!detalle} title={detalle?.item.nombre||''} onClose={()=>setDetalle(null)}>{detalle&&<div className="space-y-4">
   <div className="aspect-video overflow-hidden rounded-2xl bg-slate-100"><img src={detalle.item.imagen_url||FALLBACK_IMG} onError={e=>{(e.currentTarget as HTMLImageElement).src=FALLBACK_IMG}} className="h-full w-full object-cover" alt={detalle.item.nombre}/></div>
   <p className="text-xs font-bold uppercase tracking-wider text-violet-600">{detalle.tipo==='servicio'?(detalle.item.categoria_nombre||'Servicio'):(detalle.item.marca||detalle.item.categoria_nombre||'Producto')}</p>
   <p className="text-slate-600 dark:text-slate-300">{detalle.item.descripcion||'Sin descripción disponible.'}</p>
   <div className="flex items-center justify-between rounded-2xl bg-violet-50 p-4 dark:bg-violet-950/30">
    {detalle.tipo==='servicio'&&<span className="flex items-center gap-1.5 text-sm text-slate-500"><Clock size={15}/>{detalle.item.duracion_minutos} minutos</span>}
    <b className="text-xl text-violet-700">S/ {Number(detalle.item.precio).toFixed(2)}</b>
   </div>
   <Link to={ctaHref} onClick={()=>setDetalle(null)} className="btn-primary w-full !py-3">{detalle.tipo==='servicio'?'Crear cuenta y reservar':'Crear cuenta y comprar'}</Link>
   <p className="text-center text-xs text-slate-400">¿Ya tienes cuenta? <Link to={`/login?next=${encodeURIComponent(detalle.tipo==='servicio'?`/cliente/agendar?servicio=${detalle.item.id}`:'/cliente/tienda')}`} onClick={()=>setDetalle(null)} className="text-violet-600 underline">Inicia sesión</Link></p>
  </div>}</Modal>

  <ChatWidget/>
 </div>
}
