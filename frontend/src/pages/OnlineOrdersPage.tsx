import{useState}from'react';import{useMutation,useQuery,useQueryClient}from'@tanstack/react-query';import{http,errorMessage}from'../api/http';import toast from'react-hot-toast';import{StatusBadge}from'../components/StatusBadge';import{Package,Truck,Store}from'lucide-react';
const money=(v:any)=>new Intl.NumberFormat('es-PE',{style:'currency',currency:'PEN'}).format(Number(v||0));
const SIGUIENTE:Record<string,{estado:string;label:string}>={PENDIENTE:{estado:'CONFIRMADO',label:'Confirmar pedido'},CONFIRMADO:{estado:'LISTO',label:'Marcar listo'},LISTO:{estado:'ENTREGADO',label:'Marcar entregado'}};
export function OnlineOrdersPage(){
 const qc=useQueryClient();const[filtro,setFiltro]=useState('');
 const{data,isLoading}=useQuery({queryKey:['online-orders',filtro],queryFn:async()=>{const r=await http.get('/online-orders',{params:{estado:filtro||undefined}});return r.data.data}});
 const cambiar=useMutation({mutationFn:({id,estado}:{id:string;estado:string})=>http.patch(`/online-orders/${id}/status`,null,{params:{estado}}),onSuccess:()=>{toast.success('Pedido actualizado');qc.invalidateQueries({queryKey:['online-orders']})},onError:e=>toast.error(errorMessage(e))});
 const items=data?.items||[];
 return <div className="space-y-5">
  <div><h1 className="page-title">Pedidos de la tienda</h1><p className="text-slate-500">Pedidos de productos hechos por clientes desde el portal — pago en salón.</p></div>
  <div className="flex gap-2 overflow-auto">{[['','Todos'],['PENDIENTE','Pendientes'],['CONFIRMADO','Confirmados'],['LISTO','Listos'],['ENTREGADO','Entregados'],['CANCELADO','Cancelados']].map(([v,l])=><button key={v} onClick={()=>setFiltro(v)} className={`whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-bold ${filtro===v?'bg-violet-600 text-white':'bg-slate-100 dark:bg-slate-800'}`}>{l}</button>)}</div>
  <div className="grid gap-3">{isLoading?<div className="card">Cargando pedidos...</div>:items.length===0?<div className="card py-12 text-center text-slate-500">No hay pedidos en este filtro.</div>:items.map((x:any)=><div className="card" key={x.id}>
   <div className="flex flex-wrap items-start justify-between gap-3">
    <div><p className="font-bold">{x.codigo} · {x.cliente_nombre}</p><p className="text-sm text-slate-500">{new Date(x.fecha).toLocaleString('es-PE')}</p>
     <p className="mt-1 flex items-center gap-1 text-sm text-slate-500">{x.modalidad_entrega==='RECOJO_SALON'?<Store size={14}/>:<Truck size={14}/>}{x.modalidad_entrega==='RECOJO_SALON'?'Recojo en salón':`Entrega a domicilio${x.direccion_entrega?': '+x.direccion_entrega:''}`} · {x.metodo_pago==='PAGO_EN_SALON'?'Pago en salón':x.metodo_pago}</p>
    </div>
    <div className="text-right"><StatusBadge value={x.estado}/><p className="mt-2 text-xl font-black text-violet-700">{money(x.total)}</p></div>
   </div>
   <div className="mt-3 space-y-1 border-t pt-3 text-sm">{x.items.map((it:any)=><div className="flex justify-between" key={it.producto_id}><span>{it.cantidad} × {it.nombre}</span><span>{money(it.subtotal)}</span></div>)}</div>
   {x.notas&&<p className="mt-2 rounded-lg bg-slate-50 p-2 text-sm text-slate-500 dark:bg-slate-900">Nota: {x.notas}</p>}
   <div className="mt-3 flex flex-wrap gap-2 border-t pt-3">
    {SIGUIENTE[x.estado]&&<button className="btn-primary !px-3 !py-2" onClick={()=>cambiar.mutate({id:x.id,estado:SIGUIENTE[x.estado].estado})}><Package size={16}/>{SIGUIENTE[x.estado].label}</button>}
    {['PENDIENTE','CONFIRMADO','LISTO'].includes(x.estado)&&<button className="btn-secondary !px-3 !py-2 text-rose-600" onClick={()=>confirm('¿Cancelar este pedido?')&&cambiar.mutate({id:x.id,estado:'CANCELADO'})}>Cancelar pedido</button>}
   </div>
  </div>)}</div>
 </div>
}
