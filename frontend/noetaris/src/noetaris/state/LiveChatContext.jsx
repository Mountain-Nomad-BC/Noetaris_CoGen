import React,{createContext,useContext,useEffect,useRef,useSyncExternalStore} from 'react';
import { LiveChatStore } from '../services/liveChatStore';
const Context=createContext(null);
export function LiveChatProvider({children}){
  const store=useRef(null);if(!store.current)store.current=new LiveChatStore();
  useEffect(()=>{const clear=()=>store.current.reset();window.addEventListener('noetaris-identity-cleared',clear);return()=>{window.removeEventListener('noetaris-identity-cleared',clear);store.current.reset();};},[]);
  return <Context.Provider value={store.current}>{children}</Context.Provider>;
}
export function useLiveChat(){const store=useContext(Context);if(!store)throw new Error('LiveChatProvider is required');return {...useSyncExternalStore(store.subscribe,store.snapshot),store};}
