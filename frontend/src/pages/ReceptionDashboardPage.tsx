import {useQuery} from '@tanstack/react-query';
import {http} from '../api/http';
import {Link} from 'react-router-dom';
import {CalendarDays, CircleDollarSign, Clock3, UserPlus, Package, ReceiptText} from 'lucide-react';
import {localToday} from '../utils/date';

const today=localToday;
const money=(v:any)=>new Intl.NumberFormat('es-PE',{style:'currency',currency:'PEN'}).format(Number(v||0));
const unwrap=(r:any)=>r?.data?.data??r?.data;

export function ReceptionDashboardPage(){
 const date=today();
 const {data:summary}=useQuery({queryKey:['reception-summary',date],queryFn:async()=>unwrap(await http.get('/appointments/summary',{params:{fecha:date}}))});
 const {data:pending=[]}=useQuery({queryKey:['pending-charges'],queryFn:async()=>unwrap(await http.get('/finance/pending-charges'))||[]});
 const {data:orders}=useQuery({queryKey:['online-orders',''],queryFn:async()=>unwrap(await http.get('/online-orders'))});
 const pendingTotal=(pending||[]).reduce((a:number,x:any)=>a+Number(x.precio_total||0),0);
 const pendingOrders=(orders?.items||[]).filter((x:any)=>['PENDIENTE','CONFIRMADO','LISTO'].includes(x.estado));
 const cards=[
  [CalendarDays,'Citas de hoy',summary?.total_citas||0,'/agenda'],
  [Clock3,'Pendientes',summary?.pendientes||0,'/agenda'],
  [ReceiptText,'Pendientes de cobro',pending?.length||0,'/pos'],
  [CircleDollarSign,'Monto por cobrar',money(pendingTotal),'/pos'],
 ] as const;
 return <div className="space-y-6">
  <div><h1 className="page-title">Panel de recepción</h1><p className="text-slate-500">Agenda, clientes, cobros y pedidos del día.</p></div>
  <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([Icon,label,value,to])=><Link to={to} className="card transition hover:-translate-y-1 hover:border-violet-400" key={label}><div className="mb-4 grid h-11 w-11 place-items-center rounded-xl bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300"><Icon/></div><p className="text-sm text-slate-500">{label}</p><p className="mt-1 text-2xl font-bold">{value}</p></Link>)}</div>
  <div className="grid gap-5 lg:grid-cols-3">
   <section className="card lg:col-span-2"><div className="mb-4 flex items-center justify-between"><div><h2 className="font-bold">Cobros pendientes</h2><p className="text-sm text-slate-500">Citas finalizadas que aún no tienen venta.</p></div><Link className="btn-primary" to="/pos">Ir al POS</Link></div><div className="space-y-3">{pending.length===0?<p className="rounded-xl bg-slate-50 p-5 text-center text-slate-500 dark:bg-slate-900">No hay cobros pendientes.</p>:pending.slice(0,6).map((x:any)=><div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border p-3 dark:border-slate-800" key={x.id}><div><p className="font-semibold">{x.cliente_nombre}</p><p className="text-sm text-slate-500">{x.fecha} · {String(x.hora_inicio).slice(0,5)} · {x.empleado_nombre}</p></div><b>{money(x.precio_total)}</b></div>)}</div></section>
   <aside className="card"><Package className="mb-3 text-violet-600" size={34}/><h2 className="font-bold">Pedidos de la tienda</h2><p className="mt-1 text-sm text-slate-500">Compras de productos hechas por clientes, con pago en salón.</p>{pendingOrders.length===0?<p className="mt-4 rounded-xl bg-slate-50 p-4 text-center text-sm text-slate-500 dark:bg-slate-900">No hay pedidos por atender.</p>:<div className="mt-4 space-y-2">{pendingOrders.slice(0,4).map((x:any)=><div key={x.id} className="flex items-center justify-between rounded-lg border p-2 text-sm dark:border-slate-800"><span>{x.codigo}</span><b>{money(x.total)}</b></div>)}</div>}<Link className="btn-primary mt-4 w-full justify-center" to="/pedidos">{pendingOrders.length>0?`Atender ${pendingOrders.length} pedido(s)`:'Ver pedidos'}</Link></aside>
  </div>
  <div className="grid gap-3 sm:grid-cols-3"><Link to="/clientes" className="btn-secondary justify-center"><UserPlus size={18}/>Registrar cliente</Link><Link to="/agenda" className="btn-secondary justify-center"><CalendarDays size={18}/>Nueva cita</Link><Link to="/pos" className="btn-secondary justify-center"><ReceiptText size={18}/>Registrar cobro</Link></div>
 </div>
}
