import {Navigate} from 'react-router-dom';
import {useAuth} from '../auth/AuthContext';
import type {ReactNode} from 'react';

export function RoleRoute({roles,children}:{roles:string[];children:ReactNode}){
  const {user}=useAuth();
  if(!user)return <Navigate to="/login" replace/>;
  if(!roles.includes(user.rol)){
    const fallback=user.rol==='CLIENTE'?'/cliente':user.rol==='ESTILISTA'?'/agenda':'/';
    return <Navigate to={fallback} replace/>;
  }
  return <>{children}</>;
}
