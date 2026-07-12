import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { http, errorMessage } from '../api/http';
import toast from 'react-hot-toast';
import { Modal } from '../components/Modal';
import { Pagination } from '../components/Pagination';
import { StatusBadge } from '../components/StatusBadge';
import type { Client, Paginated } from '../types';
import { Eye, KeyRound, Pencil, Plus, Power, RotateCcw, Search, Trash2, UserCheck, UserX } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';

const blank = { nombres:'', apellidos:'', documento:'', telefono:'', correo:'', direccion:'', fecha_nacimiento:'', observaciones:'', preferencias:'', alergias:'', crear_acceso_portal:false, password_portal:'' };
const clean = (value:any) => Object.fromEntries(Object.entries(value).map(([k,v]) => [k, v === '' ? null : v]));

export function ClientsPage() {
  const { user } = useAuth();
  const isAdmin = user?.rol === 'ADMINISTRADOR';
  const canEdit = isAdmin || user?.rol === 'RECEPCIONISTA';
  const [page,setPage] = useState(1);
  const [q,setQ] = useState('');
  const [estado,setEstado] = useState('');
  const [open,setOpen] = useState(false);
  const [detail,setDetail] = useState<Client|null>(null);
  const [form,setForm] = useState<any>(blank);
  const [editing,setEditing] = useState<string|null>(null);
  const [credential,setCredential] = useState<{correo:string,password:string}|null>(null);
  const qc = useQueryClient();
  const invalidate = () => qc.invalidateQueries({queryKey:['clients']});

  const {data,isLoading} = useQuery({queryKey:['clients',page,q,estado],queryFn:async()=>{
    const {data}=await http.get<Paginated<Client>>('/clients',{params:{pagina:page,tamano_pagina:10,busqueda:q||undefined,estado:estado||undefined}}); return data;
  }});

  const save = useMutation({mutationFn:()=>editing?http.put(`/clients/${editing}`,clean({...form,crear_acceso_portal:undefined,password_portal:undefined})):http.post('/clients',clean(form)),onSuccess:()=>{toast.success('Cliente guardado');close();invalidate()},onError:e=>toast.error(errorMessage(e))});
  const status = useMutation({mutationFn:({id,value}:{id:string,value:string})=>http.patch(`/clients/${id}/status`,{estado:value}),onSuccess:()=>{toast.success('Estado actualizado');invalidate()},onError:e=>toast.error(errorMessage(e))});
  const archive = useMutation({mutationFn:(id:string)=>http.delete(`/clients/${id}`),onSuccess:()=>{toast.success('Cliente archivado');invalidate()},onError:e=>toast.error(errorMessage(e))});
  const createPortal = useMutation({mutationFn:({id,password}:{id:string,password?:string})=>http.post(`/clients/${id}/portal-access`,{password:password||null}),onSuccess:r=>{const d=r.data.data; toast.success('Acceso creado'); if(d.password_temporal)setCredential({correo:d.correo,password:d.password_temporal}); invalidate()},onError:e=>toast.error(errorMessage(e))});
  const portalStatus = useMutation({mutationFn:({id,value}:{id:string,value:string})=>http.patch(`/clients/${id}/portal-access/status`,{estado:value}),onSuccess:()=>{toast.success('Acceso actualizado');invalidate()},onError:e=>toast.error(errorMessage(e))});
  const resetPortal = useMutation({mutationFn:(id:string)=>http.post(`/clients/${id}/portal-access/reset-password`),onSuccess:r=>{const d=r.data.data;setCredential({correo:d.correo,password:d.password_temporal});toast.success('Contraseña temporal generada')},onError:e=>toast.error(errorMessage(e))});
  const deletePortal = useMutation({mutationFn:(id:string)=>http.delete(`/clients/${id}/portal-access`),onSuccess:()=>{toast.success('Acceso eliminado');invalidate()},onError:e=>toast.error(errorMessage(e))});

  const close=()=>{setOpen(false);setEditing(null);setForm(blank)};
  const edit=(x:Client)=>{setEditing(x.id);setForm({...blank,...x,crear_acceso_portal:false,password_portal:''});setOpen(true)};
  const askCreatePortal=(x:Client)=>{const password=prompt('Contraseña inicial (deja vacío para generar una temporal):')||undefined;createPortal.mutate({id:x.id,password})};

  return <div className="space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="page-title">Clientes</h1><p className="text-slate-500">Ficha del cliente y acceso al portal en un solo lugar.</p></div>{canEdit&&<button className="btn-primary" onClick={()=>setOpen(true)}><Plus size={18}/>Nuevo cliente</button>}</div>
    <div className="card grid gap-3 md:grid-cols-[1fr_220px]"><div className="relative"><Search className="absolute left-3 top-2.5 text-slate-400" size={19}/><input className="field pl-10" placeholder="Buscar por nombre, documento o correo" value={q} onChange={e=>{setQ(e.target.value);setPage(1)}}/></div><select className="field" value={estado} onChange={e=>setEstado(e.target.value)}><option value="">Todos los estados</option><option>ACTIVO</option><option>INACTIVO</option></select></div>
    <div className="table-wrap"><table><thead><tr><th>Cliente</th><th>Contacto</th><th>Portal</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{isLoading?<tr><td colSpan={5}>Cargando...</td></tr>:(data?.items||[]).map(x=><tr key={x.id}><td><b>{x.nombre_completo}</b><div className="text-xs text-slate-400">{x.documento||'Sin documento'}</div></td><td>{x.telefono||'—'}<div className="text-xs">{x.correo||'Sin correo'}</div></td><td>{x.usuario_id?<div><StatusBadge value={x.portal_estado||'INACTIVO'}/><div className="mt-1 text-xs text-slate-400">{x.portal_ultimo_login?`Último acceso: ${new Date(x.portal_ultimo_login).toLocaleString()}`:'Nunca ingresó'}</div></div>:<span className="text-sm text-slate-400">Sin acceso</span>}</td><td><StatusBadge value={x.estado}/></td><td><div className="flex flex-wrap gap-1"><button className="btn-secondary !p-2" onClick={()=>setDetail(x)} title="Ver"><Eye size={16}/></button>{canEdit&&<><button className="btn-secondary !p-2" onClick={()=>edit(x)} title="Editar"><Pencil size={16}/></button><button className="btn-secondary !p-2" onClick={()=>status.mutate({id:x.id,value:x.estado==='ACTIVO'?'INACTIVO':'ACTIVO'})} title="Cambiar estado">{x.estado==='ACTIVO'?<Power size={16}/>:<RotateCcw size={16}/>}</button>{!x.usuario_id?<button className="btn-secondary !p-2 text-emerald-600" onClick={()=>askCreatePortal(x)} title="Crear acceso"><UserCheck size={16}/></button>:<><button className="btn-secondary !p-2" onClick={()=>resetPortal.mutate(x.id)} title="Restablecer contraseña"><KeyRound size={16}/></button><button className="btn-secondary !p-2" onClick={()=>portalStatus.mutate({id:x.id,value:x.portal_estado==='ACTIVO'?'INACTIVO':'ACTIVO'})} title="Activar/Inactivar portal">{x.portal_estado==='ACTIVO'?<UserX size={16}/>:<UserCheck size={16}/>}</button></>}</>}{isAdmin&&<><button className="btn-secondary !p-2 text-rose-600" onClick={()=>confirm('¿Archivar este cliente?')&&archive.mutate(x.id)} title="Archivar cliente"><Trash2 size={16}/></button>{x.usuario_id&&<button className="btn-secondary !p-2 text-rose-600" onClick={()=>confirm('¿Eliminar únicamente el acceso al portal?')&&deletePortal.mutate(x.id)} title="Eliminar acceso"><UserX size={16}/></button>}</>}</div></td></tr>)}</tbody></table></div>
    <Pagination page={page} total={data?.total_paginas||1} onChange={setPage}/>

    <Modal open={open} title={editing?'Editar cliente':'Nuevo cliente'} onClose={close}><form className="grid gap-4 sm:grid-cols-2" onSubmit={e=>{e.preventDefault();save.mutate()}}>{[['nombres','Nombres','text'],['apellidos','Apellidos','text'],['documento','Documento','text'],['telefono','Teléfono','text'],['correo','Correo','email'],['direccion','Dirección','text'],['fecha_nacimiento','Fecha de nacimiento','date'],['preferencias','Preferencias','text'],['alergias','Alergias','text'],['observaciones','Observaciones','text']].map(([k,l,t])=><label key={k} className={['observaciones','preferencias','alergias'].includes(k)?'sm:col-span-2':''}><span className="label">{l}</span>{['observaciones','preferencias','alergias'].includes(k)?<textarea className="field" value={form[k]||''} onChange={e=>setForm({...form,[k]:e.target.value})}/>:<input className="field" type={t} value={form[k]||''} onChange={e=>setForm({...form,[k]:e.target.value})} required={k==='nombres'||k==='apellidos'}/>}</label>)}{!editing&&<div className="sm:col-span-2 rounded-xl border p-4"><label className="flex items-center gap-2 font-semibold"><input type="checkbox" checked={form.crear_acceso_portal} onChange={e=>setForm({...form,crear_acceso_portal:e.target.checked})}/>Crear acceso al portal del cliente</label>{form.crear_acceso_portal&&<div className="mt-3"><span className="label">Contraseña inicial (opcional)</span><input className="field" type="password" value={form.password_portal||''} onChange={e=>setForm({...form,password_portal:e.target.value})} placeholder="Vacío = contraseña temporal"/><p className="mt-1 text-xs text-slate-400">El correo es obligatorio. Si se deja vacío, el sistema genera una contraseña temporal.</p></div>}</div>}<div className="sm:col-span-2 flex justify-end gap-2"><button type="button" className="btn-secondary" onClick={close}>Cancelar</button><button className="btn-primary" disabled={save.isPending}>Guardar cambios</button></div></form></Modal>

    <Modal open={!!detail} title="Detalle del cliente" onClose={()=>setDetail(null)}>{detail&&<div className="grid gap-3 sm:grid-cols-2">{Object.entries({Nombre:detail.nombre_completo,Documento:detail.documento,Teléfono:detail.telefono,Correo:detail.correo,Dirección:detail.direccion,'Fecha de nacimiento':detail.fecha_nacimiento,Preferencias:detail.preferencias,Alergias:detail.alergias,Observaciones:detail.observaciones,Estado:detail.estado,'Acceso portal':detail.usuario_id?detail.portal_estado:'No creado','Último ingreso':detail.portal_ultimo_login?new Date(detail.portal_ultimo_login).toLocaleString():'Nunca'}).map(([k,v])=><div key={k} className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800"><div className="text-xs font-semibold uppercase text-slate-400">{k}</div><div>{v||'—'}</div></div>)}</div>}</Modal>

    <Modal open={!!credential} title="Credenciales del portal" onClose={()=>setCredential(null)}>{credential&&<div className="space-y-4"><p>Guarda y entrega estas credenciales al cliente. La contraseña solo se muestra una vez.</p><div className="rounded-xl bg-slate-100 p-4 dark:bg-slate-800"><div><b>Correo:</b> {credential.correo}</div><div><b>Contraseña temporal:</b> <code>{credential.password}</code></div></div><button className="btn-primary w-full" onClick={()=>navigator.clipboard.writeText(`Correo: ${credential.correo}\nContraseña: ${credential.password}`).then(()=>toast.success('Credenciales copiadas'))}>Copiar credenciales</button></div>}</Modal>
  </div>;
}
