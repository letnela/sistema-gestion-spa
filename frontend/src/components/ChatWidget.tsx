import {useEffect,useRef,useState} from 'react';
import {useNavigate} from 'react-router-dom';
import {http,errorMessage} from '../api/http';
import {MessageCircle,X,Send,Sparkles,Image as ImageIcon,XCircle,CalendarDays,ShoppingBag,Clock,Package} from 'lucide-react';

type Recommendation={
 tipo:'SERVICIO'|'PRODUCTO';id:string;nombre:string;descripcion?:string|null;
 imagen_url?:string|null;precio:number;duracion_minutos?:number|null;stock?:number|null;accion:'RESERVAR'|'COMPRAR'
};
type Msg={role:'user'|'assistant';content:string;imagenPreview?:string;recomendaciones?:Recommendation[];opcionesRapidas?:string[]};
const SALUDO:Msg={role:'assistant',content:'¡Hola! Soy tu asesora virtual de Elegance. ¿Qué deseas mejorar hoy?',opcionesRapidas:['Cabello','Maquillaje','Uñas','Rostro','Masajes']};
const REQUEST_TIMEOUT_MS=12000;

function getSesionId():string{
 const key='salon_chat_sesion_id';
 let id=localStorage.getItem(key);
 if(!id){id=crypto.randomUUID();localStorage.setItem(key,id)}
 return id;
}

function apiAssetUrl(value?:string|null):string{
 if(!value)return '';
 if(/^https?:\/\//i.test(value)||value.startsWith('data:'))return value;
 const api=(import.meta.env.VITE_API_URL||'http://localhost:8000/api/v1').replace(/\/api\/v1\/?$/,'');
 return `${api}${value.startsWith('/')?'':'/'}${value}`;
}

async function prepareImage(file:File):Promise<{base64:string;mediaType:string;preview:string}>{
 if(!file.type.match(/^image\/(jpeg|png|webp)$/))throw new Error('Formato no permitido');
 if(file.size>8*1024*1024)throw new Error('La imagen supera 8 MB');
 const bitmap=await createImageBitmap(file);
 const max=1280;
 const scale=Math.min(1,max/Math.max(bitmap.width,bitmap.height));
 const canvas=document.createElement('canvas');
 canvas.width=Math.max(1,Math.round(bitmap.width*scale));
 canvas.height=Math.max(1,Math.round(bitmap.height*scale));
 const ctx=canvas.getContext('2d');
 if(!ctx)throw new Error('No se pudo procesar la imagen');
 ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);
 bitmap.close();
 const blob=await new Promise<Blob>((resolve,reject)=>canvas.toBlob(b=>b?resolve(b):reject(new Error('No se pudo comprimir la imagen')),'image/jpeg',0.82));
 const dataUrl=await new Promise<string>((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result as string);reader.onerror=()=>reject(new Error('No se pudo leer la imagen'));reader.readAsDataURL(blob)});
 return{base64:dataUrl.split(',')[1],mediaType:'image/jpeg',preview:URL.createObjectURL(blob)};
}

export function ChatWidget(){
 const navigate=useNavigate();
 const[open,setOpen]=useState(false);
 const[messages,setMessages]=useState<Msg[]>([SALUDO]);
 const[input,setInput]=useState('');
 const[sending,setSending]=useState(false);
 const[image,setImage]=useState<{base64:string;mediaType:string;preview:string}|null>(null);
 const[loadedHistory,setLoadedHistory]=useState(false);
 const[thinkingText,setThinkingText]=useState('Analizando tu consulta...');
 const sesionId=useRef(getSesionId());
 const bottomRef=useRef<HTMLDivElement>(null);
 const fileRef=useRef<HTMLInputElement>(null);
 const controllerRef=useRef<AbortController|null>(null);

 useEffect(()=>()=>controllerRef.current?.abort(),[]);
 useEffect(()=>{if(!open||loadedHistory)return;(async()=>{try{const{data}=await http.get(`/public/chat/${sesionId.current}`,{timeout:6000});const historial=(data.data||[]) as{role:'user'|'assistant';content:string}[];if(historial.length>0)setMessages(historial)}catch{/* conserva saludo */}finally{setLoadedHistory(true)}})()},[open,loadedHistory]);
 useEffect(()=>{if(open)bottomRef.current?.scrollIntoView({behavior:'smooth'})},[messages,open,sending,thinkingText]);
 useEffect(()=>{if(!sending)return;const timers=[window.setTimeout(()=>setThinkingText('Revisando el catálogo del salón...'),1800),window.setTimeout(()=>setThinkingText('Preparando tus recomendaciones...'),5000)];return()=>timers.forEach(clearTimeout)},[sending]);

 const pickImage=async(e:React.ChangeEvent<HTMLInputElement>)=>{
  const file=e.target.files?.[0];if(!file)return;
  try{if(image?.preview)URL.revokeObjectURL(image.preview);setImage(await prepareImage(file))}
  catch(err:any){alert(err?.message||'No se pudo cargar la imagen')}
  finally{if(fileRef.current)fileRef.current.value=''}
 };

 const goToRecommendation=(r:Recommendation)=>{
  setOpen(false);
  const token=localStorage.getItem('access_token');
  if(!token){navigate('/registro-cliente');return}
  if(r.tipo==='SERVICIO')navigate(`/cliente/agendar?servicio_id=${encodeURIComponent(r.id)}`);
  else navigate(`/cliente/tienda?producto_id=${encodeURIComponent(r.id)}`);
 };

 const send=async(quickText?:string)=>{
  const text=(quickText??input).trim();if((!text&&!image)||sending)return;
  const sentImage=image;
  setMessages(v=>[...v,{role:'user',content:text||'Foto enviada para recibir una recomendación',imagenPreview:sentImage?.preview}]);
  setInput('');setImage(null);setSending(true);setThinkingText(sentImage?'Analizando la imagen...':'Analizando tu consulta...');
  const controller=new AbortController();controllerRef.current=controller;
  try{
   const{data}=await http.post('/public/chat',{sesion_id:sesionId.current,mensaje:text,imagen_base64:sentImage?.base64,imagen_media_type:sentImage?.mediaType},{signal:controller.signal,timeout:REQUEST_TIMEOUT_MS});
   setMessages(v=>[...v,{role:'assistant',content:data.data.respuesta,recomendaciones:data.data.recomendaciones||[],opcionesRapidas:data.data.opciones_rapidas||[]}]);
  }catch(e:any){
   const timeout=e?.code==='ECONNABORTED'||e?.name==='CanceledError';
   setMessages(v=>[...v,{role:'assistant',content:timeout?'La consulta tardó demasiado. Intenta nuevamente con una descripción corta de lo que deseas mejorar.':errorMessage(e)}]);
  }finally{controllerRef.current=null;setSending(false)}
 };

 return <>
  <button onClick={()=>setOpen(v=>!v)} className="fixed bottom-5 right-5 z-40 grid h-14 w-14 place-items-center rounded-full bg-violet-600 text-white shadow-2xl transition hover:scale-105" aria-label="Abrir chat">{open?<X size={22}/>:<MessageCircle size={22}/>}</button>
  {open&&<div className="fixed bottom-24 right-3 z-40 flex h-[min(650px,78vh)] w-[min(410px,94vw)] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900 sm:right-5">
   <div className="flex items-center gap-2 bg-gradient-to-r from-violet-600 to-fuchsia-600 px-5 py-4 text-white"><Sparkles size={18}/><div><p className="font-black leading-none">Asistente Elegance</p><p className="mt-1 text-xs text-white/80">Especializado solo en nuestro salón</p></div></div>
   <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
    {messages.map((m,i)=><div key={i} className={`flex ${m.role==='user'?'justify-end':'justify-start'}`}><div className={`max-w-[92%] ${m.role==='user'?'rounded-2xl bg-violet-600 px-3.5 py-2.5 text-white':'w-full'}`}>
     {m.role==='user'?<><>{m.imagenPreview&&<img src={m.imagenPreview} alt="Imagen enviada" className="mb-2 max-h-44 w-full rounded-xl object-cover"/>}</><p className="whitespace-pre-wrap text-sm">{m.content}</p></>:<>
      <div className="inline-block max-w-[88%] whitespace-pre-wrap rounded-2xl bg-slate-100 px-3.5 py-2.5 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200">{m.content}</div>
      {!!m.opcionesRapidas?.length&&<div className="mt-3 flex flex-wrap gap-2">{m.opcionesRapidas.map(option=><button key={option} onClick={()=>send(option)} disabled={sending} className="rounded-full border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-bold text-violet-700 transition hover:bg-violet-100 disabled:opacity-50 dark:border-violet-800 dark:bg-violet-950/40 dark:text-violet-300">{option}</button>)}</div>}
      {!!m.recomendaciones?.length&&<div className="mt-3 flex snap-x gap-3 overflow-x-auto pb-2">{m.recomendaciones.map(r=><article key={`${r.tipo}-${r.id}`} className="min-w-[230px] max-w-[230px] snap-start overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-850">
       {r.imagen_url?<img src={apiAssetUrl(r.imagen_url)} alt={r.nombre} className="h-28 w-full object-cover"/>:<div className="grid h-28 place-items-center bg-gradient-to-br from-violet-100 to-fuchsia-100 text-violet-500"><Sparkles size={28}/></div>}
       <div className="p-3"><span className="text-[10px] font-black uppercase tracking-wider text-violet-600">{r.tipo==='SERVICIO'?'Servicio':'Producto'}</span><h4 className="mt-1 line-clamp-2 text-sm font-black text-slate-800 dark:text-white">{r.nombre}</h4><p className="mt-1 line-clamp-2 text-xs text-slate-500">{r.descripcion||'Disponible en nuestro salón'}</p>
        <div className="mt-2 flex items-center justify-between text-xs text-slate-500"><strong className="text-base text-slate-900 dark:text-white">S/ {Number(r.precio).toFixed(2)}</strong>{r.tipo==='SERVICIO'&&r.duracion_minutos?<span className="flex items-center gap-1"><Clock size={13}/>{r.duracion_minutos} min</span>:r.stock!=null?<span className="flex items-center gap-1"><Package size={13}/>{r.stock} disponibles</span>:null}</div>
        <button onClick={()=>goToRecommendation(r)} className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-violet-600 px-3 py-2 text-xs font-bold text-white hover:bg-violet-700">{r.tipo==='SERVICIO'?<CalendarDays size={15}/>:<ShoppingBag size={15}/>} {r.tipo==='SERVICIO'?'Reservar':'Comprar'}</button>
       </div>
      </article>)}</div>}
     </>}
    </div></div>)}
    {sending&&<div className="flex justify-start"><div className="rounded-2xl bg-slate-100 px-3.5 py-2.5 text-sm text-slate-500 dark:bg-slate-800 dark:text-slate-300"><span className="mr-2 inline-flex gap-1 align-middle"><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current"/><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:120ms]"/><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-current [animation-delay:240ms]"/></span>{thinkingText}</div></div>}
    <div ref={bottomRef}/>
   </div>
   {image&&<div className="flex items-center gap-2 border-t px-3 pt-3 dark:border-slate-800"><img src={image.preview} alt="Vista previa" className="h-14 w-14 rounded-xl object-cover"/><div><p className="text-xs font-bold text-slate-700 dark:text-slate-200">Imagen lista</p><p className="text-[11px] text-slate-500">Agrega una descripción para mejorar la recomendación</p></div><button onClick={()=>{URL.revokeObjectURL(image.preview);setImage(null)}} className="ml-auto text-rose-500"><XCircle size={18}/></button></div>}
   <div className="flex items-center gap-2 border-t p-3 dark:border-slate-800"><input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={pickImage}/><button onClick={()=>fileRef.current?.click()} disabled={sending} className="icon-btn shrink-0" aria-label="Adjuntar imagen"><ImageIcon size={19}/></button><input className="field" placeholder="Pregunta sobre cabello, uñas, rostro..." value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}} disabled={sending}/><button onClick={()=>send()} disabled={sending||(!input.trim()&&!image)} className="btn-primary !p-2.5" aria-label="Enviar"><Send size={17}/></button></div>
  </div>}
 </>;
}
