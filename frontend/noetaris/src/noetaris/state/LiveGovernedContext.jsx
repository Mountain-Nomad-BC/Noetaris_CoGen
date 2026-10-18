import React,{createContext,useContext,useEffect,useRef,useSyncExternalStore} from 'react';
import {LiveGovernedStore} from '../services/liveGovernedStore';
const Context=createContext(null);
export function LiveGovernedProvider({children}){
 const store=useRef(null);if(!store.current)store.current=new LiveGovernedStore();
 useEffect(()=>{const clear=()=>store.current.reset();window.addEventListener('noetaris-identity-cleared',clear);return()=>{window.removeEventListener('noetaris-identity-cleared',clear);store.current.reset();};},[]);
 return <Context.Provider value={store.current}>{children}</Context.Provider>;
}
export function useLiveGoverned(){const store=useContext(Context);if(!store)throw new Error('LiveGovernedProvider is required');return {...useSyncExternalStore(store.subscribe,store.snapshot),store};}
