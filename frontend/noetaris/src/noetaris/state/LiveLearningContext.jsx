import React,{createContext,useContext,useEffect,useRef,useSyncExternalStore} from 'react';
import {LiveLearningStore} from '../services/liveLearningStore';
const Context=createContext(null);
export function LiveLearningProvider({children}){
 const store=useRef(null);if(!store.current)store.current=new LiveLearningStore();
 useEffect(()=>{const reset=()=>store.current.reset();window.addEventListener('noetaris-identity-cleared',reset);return()=>{window.removeEventListener('noetaris-identity-cleared',reset);store.current.reset();};},[]);
 return <Context.Provider value={store.current}>{children}</Context.Provider>;
}
export function useLiveLearning(){const store=useContext(Context);if(!store)throw new Error('LiveLearningProvider is required');return {...useSyncExternalStore(store.subscribe,store.snapshot),store};}
