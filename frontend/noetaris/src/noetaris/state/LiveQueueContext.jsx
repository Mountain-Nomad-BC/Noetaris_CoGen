import React,{createContext,useContext,useEffect,useRef,useSyncExternalStore} from 'react';
import {LiveQueueStore} from '../services/liveQueueStore';
const Context=createContext(null);
export function LiveQueueProvider({children}){const store=useRef(null);if(!store.current)store.current=new LiveQueueStore();useEffect(()=>{const clear=()=>store.current.reset();window.addEventListener('noetaris-identity-cleared',clear);return()=>{window.removeEventListener('noetaris-identity-cleared',clear);store.current.reset();};},[]);return <Context.Provider value={store.current}>{children}</Context.Provider>;}
export function useLiveQueue(){const store=useContext(Context);if(!store)throw new Error('LiveQueueProvider is required');return {...useSyncExternalStore(store.subscribe,store.snapshot),store};}
