import axios from 'axios';
const baseURL=import.meta.env.VITE_API_URL||'http://localhost:8000/api/v1';
export const http=axios.create({baseURL,headers:{'Content-Type':'application/json'}});
http.interceptors.request.use(c=>{const t=localStorage.getItem('access_token');if(t)c.headers.Authorization=`Bearer ${t}`;return c});
http.interceptors.response.use(r=>r,async e=>{const original=e.config;if(e.response?.status===401&&!original?._retry&&localStorage.getItem('refresh_token')){original._retry=true;try{const {data}=await axios.post(`${baseURL}/auth/refresh`,{refresh_token:localStorage.getItem('refresh_token')});localStorage.setItem('access_token',data.access_token);localStorage.setItem('refresh_token',data.refresh_token);original.headers.Authorization=`Bearer ${data.access_token}`;return http(original)}catch{localStorage.clear();location.href='/login'}}return Promise.reject(e)});
export const errorMessage=(e:any)=>e?.response?.data?.detail||e?.response?.data?.mensaje||e?.message||'Ocurrió un error';
