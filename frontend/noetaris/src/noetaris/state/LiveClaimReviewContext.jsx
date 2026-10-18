import React,{createContext,useContext,useEffect,useRef,useSyncExternalStore} from 'react';
import {LiveClaimReviewStore} from '../services/liveClaimReviewStore';
const Context=createContext(null);
export function LiveClaimReviewProvider({children}){const store=useRef(null);if(!store.current)store.current=new LiveClaimReviewStore();useEffect(()=>{const clear=()=>store.current.reset();window.addEventListener('noetaris-identity-cleared',clear);return()=>{window.removeEventListener('noetaris-identity-cleared',clear);store.current.reset();};},[]);return <Context.Provider value={store.current}>{children}</Context.Provider>;}
export function useLiveClaimReview(){const store=useContext(Context);if(!store)throw new Error('LiveClaimReviewProvider is required');return {...useSyncExternalStore(store.subscribe,store.snapshot),store};}
